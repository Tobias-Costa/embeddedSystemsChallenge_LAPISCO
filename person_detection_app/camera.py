import cv2
from ultralytics import YOLO
from collections import defaultdict
import time
import numpy as np

# Inicialização do modelo YOLO otimizado com OpenVINO
model = YOLO("yolo_models/yolo26n.pt")

# Estruturas para rastreamento de histórico e movimentação dos objetos
track_history = defaultdict(lambda: [])
last_positions = {}

def draw_fps(frame, fps):
    """Renderiza o contador de FPS no canto superior esquerdo do frame."""
    cv2.putText(frame, f"FPS: {int(fps)}", (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    return frame

def convert_frame2bytes(frame):
    """Codifica o frame no formato JPEG e converte para array de bytes."""
    success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        print("Erro: Não foi possível transformar o quadro em buffer '.jpg'")
        return None

    return buffer.tobytes()

def calculate_distance(p1, p2):
    """Calcula a distância euclidiana entre dois pontos bidimensionais."""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1]-p2[1])**2)

def generate_stream():
    """Gerador para captura de vídeo, processamento de rastreamento e mapa de calor."""
    try:
        cap = cv2.VideoCapture(0)     
        # Matriz acumuladora para geração do mapa de calor (Heatmap)
        heatmap = np.zeros((int(cap.get(4)), int(cap.get(3)), 3), dtype=np.float32) 

        while True:
            # Mecanismo de contingência e reconexão da câmera
            if not cap.isOpened():
                print("Não foi possível acessar a câmera. Reiniciando a câmera...")
                cap = cv2.VideoCapture(0)
                continue
        
            success, frame = cap.read()

            if not success:
                print("Erro de leitura. Reiniciando câmera...")
                cap.release()
                cap = cv2.VideoCapture(0)
                continue
    
            start_time = time.time()
            
            # Inferência do YOLO restringindo a detecção apenas para pessoas (classe 0)
            results = model.track(frame, persist=True, classes=[0], imgsz=320) #, conf=0.8
            result = results[0]

            # Validação e desenho das caixas delimitadoras (bounding boxes)
            if result.boxes is not None and result.boxes.id is not None:
                annotated_frame = result.plot()
                boxes = result.boxes.xywh.cpu()
                tracks_ids = result.boxes.id.int().cpu().tolist()

                for box, track_id in zip(boxes, tracks_ids):
                    track_id = int(track_id)
                    x_center, y_center, width, height = box
                    current_position = (float(x_center), float(y_center))

                    # Conversão e normalização das coordenadas para os limites da matriz
                    top_left_x = max(0, int(x_center - width / 2))
                    top_left_y = max(0, int(y_center - height / 2))
                    bottom_right_x = min(heatmap.shape[1], int(x_center + width / 2))
                    bottom_right_y = min(heatmap.shape[0], int(y_center + height / 2))

                    # Atualização do histórico de rastreamento com teto de 1200 registros
                    track = track_history[track_id]
                    track.append(current_position)
                    if len(track) > 1200:
                        track.pop(0)

                    # Acúmulo no heatmap conforme permanência do objeto
                    heatmap[top_left_y: bottom_right_y, top_left_x: bottom_right_x] += 1
                    
                    last_positions[track_id] = current_position
            else:
                annotated_frame = frame.copy()
            
            if np.max(heatmap) > 0:
                # Tratamento visual, normalização e aplicação da escala de cor JET no heatmap
                heatmap_blurred = cv2.GaussianBlur(heatmap, (15,15), 0)
                heatmap_norm = cv2.normalize(heatmap_blurred, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
            else:
                heatmap_color =  np.zeros_like(frame, dtype=np.uint8)

            # Sobreposição (overlay) do heatmap sobre o frame original
            alpha = 0.7
            overlay = cv2.addWeighted(frame, 1-alpha, heatmap_color, alpha, 0)

            # Ajuste de escala para concatenação horizontal das imagens
            if overlay.shape != annotated_frame.shape:
                overlay = cv2.resize(annotated_frame, (overlay.shape[1], overlay.shape[0]))

            output = np.hstack((annotated_frame, overlay))

            # Cálculo de desempenho e desenho do FPS final
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            output = draw_fps(output, fps)

            frame_bytes = convert_frame2bytes(output)
            
            # Streaming via protocolo HTTP (Multipart MJPEG)
            yield (
                b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        # Liberação do recurso de hardware ao encerrar o gerador
        cap.release()
