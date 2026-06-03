import cv2
from ultralytics import YOLO
import time
import numpy as np

 # Constante de correção para evitar divisão por zero
EPS = 1e-6
# Parâmetros de decaimento do heatmap
GC_ETA = 0.3
GC_PHI = 0.3
# Constante de decremento do heatmap
HEATMAP_DECAY = 5
# Constante de multiplicação do GC
HEATMAP_GAIN = 30
# Constante para transparência do overlay
HEATMAP_ALPHA = 0.7

# Inicialização do modelo YOLO otimizado com NCNN
model = YOLO("yolo_models/yolo26n_ncnn_model")


def draw_fps(frame, fps):
    """Renderiza o contador de FPS no canto superior esquerdo do frame."""
    cv2.putText(
        frame,
        f"FPS: {int(fps)}",
        (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )
    return frame


def convert_frame2bytes(frame):
    """Codifica o frame no formato JPEG e converte para array de bytes."""
    success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        print("Erro: Não foi possível transformar o quadro em buffer '.jpg'")
        return None

    return buffer.tobytes()


def calculate_gc(top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    '''Cria matriz de centralidade generalizada.'''

    # Cria vetor contendo todos os valores de X dentro do box de detection
    xs = np.arange(top_left_x, bottom_right_x)
    # Cria vetor contendo todos os valores de Y dentro do box de detection
    ys = np.arange(top_left_y, bottom_right_y)

    # Cria matrizes dos vetores X e Y que contém todas as coordenadas do box de detection
    xx, yy = np.meshgrid(xs, ys)

    # Cálculo das distâncias do centro do box para a esquerda e direita, respecivamente
    l = xx - top_left_x
    r = bottom_right_x - xx
    # Cálculo das distâncias do centro do box para o topo e a base, respecivamente
    t = yy - top_left_y
    b = bottom_right_y - yy

   

    # Matriz de valores do heatmap(Generalized Centerness)
    gc = (
        ((np.minimum(l, r) + EPS) / (np.maximum(l, r) + EPS)) ** GC_ETA
    ) * (((np.minimum(t, b) + EPS) / (np.maximum(t, b) + EPS)) ** GC_PHI)

    return gc


def process_heatmap(heatmap, frame):
    '''Tratamento visual, normalização e aplicação da escala de cor JET no heatmap'''

    # Uso do np.clip para limitar 255 como máximo e permitir decaimento suave
    heatmap_norm = np.clip(heatmap, 0, 255).astype(np.uint8)
    heatmap_blurred = cv2.GaussianBlur(heatmap_norm, (15, 15), 0)
    heatmap_color = cv2.applyColorMap(heatmap_blurred, cv2.COLORMAP_JET)

    # Sobreposição (overlay) do heatmap sobre o frame original
    overlay = cv2.addWeighted(frame, 1 - HEATMAP_ALPHA, heatmap_color, HEATMAP_ALPHA, 0)

    return overlay


def generate_stream():
    """Gerador para captura de vídeo, processamento de rastreamento e mapa de calor."""
    try:
        cap = cv2.VideoCapture(0)
        # Matriz acumuladora para geração do mapa de calor (Heatmap)
        heatmap = np.zeros((int(cap.get(4)), int(cap.get(3))), dtype=np.float32)

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
            
            # Variável usada no cálculo do FPS
            start_time = time.time()

            # Inferência do YOLO restringindo a detecção apenas para pessoas (classe 0)
            results = model(frame, classes=[0], imgsz=320, verbose=False)  # , conf=0.8
            result = results[0]

            # Validação e desenho das caixas delimitadoras (bounding boxes)
            # Se haver detecção de caixas, caso contrário retorna frame enxuto para economizar recursos
            if result.boxes is not None:
                annotated_frame = result.plot()
                boxes = result.boxes.xywh.cpu()

                for box in boxes:
                    # Separa os valores de box para melhor legibilidade
                    x_center, y_center, width, height = box

                    # Conversão e normalização das coordenadas para os limites da matriz
                    top_left_x = max(0, int(x_center - width / 2))
                    top_left_y = max(0, int(y_center - height / 2))
                    bottom_right_x = min(heatmap.shape[1], int(x_center + width / 2))
                    bottom_right_y = min(heatmap.shape[0], int(y_center + height / 2))

                    gc = calculate_gc(top_left_x, top_left_y, bottom_right_x, bottom_right_y)

                    # Atribuição do GC à região do detection box multiplicado por 30 para rápido crescimento do heatmap
                    heatmap[top_left_y:bottom_right_y, top_left_x:bottom_right_x] += (
                        gc * HEATMAP_GAIN
                    )
            else:
                # Caso não seja detectado nimguém, o frame de detecção sera igual ao frame capturado e o heatmap não mudará
                # Através dessa condicional o processamento de frames se torna mais rápido
                annotated_frame = frame.copy()

            # Decremento dos valores do heatmap
            heatmap -= HEATMAP_DECAY

            # Ajustes do heatmap
            overlay = process_heatmap(heatmap, frame)
            
            # Ajuste de escala para concatenação horizontal das imagens
            if overlay.shape != annotated_frame.shape:
                overlay = cv2.resize(
                    overlay, (annotated_frame.shape[1], annotated_frame.shape[0])
                )

            # Concatenação dos resultados
            output = np.hstack((annotated_frame, overlay))

            # Cálculo de desempenho e desenho do FPS final
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            output = draw_fps(output, fps)

            frame_bytes = convert_frame2bytes(output)

            # Streaming via protocolo HTTP (Multipart MJPEG)
            yield (
                b"--frame\r\n"
                b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        # Liberação do recurso de hardware ao encerrar o gerador
        cap.release()
