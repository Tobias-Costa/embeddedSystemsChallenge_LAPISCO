import cv2
from ultralytics import YOLO
from ultralytics.solutions import Heatmap
import time
import numpy as np

model = YOLO("yolo_models/yolo26n_openvino_model")
heatmap = Heatmap(show=False, model=model, colormap=cv2.COLORMAP_PARULA, conf=0.80)

def draw_fps(frame, fps):
    cv2.putText(frame, f"FPS: {int(fps)}", (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
    return frame

def convert_frame2bytes(frame):
    success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        print("Erro: Não foi possível transformar o quadro em buffer '.jpg'")
        return None

    return buffer.tobytes()

def process_frame(frame, mode, start_time):

    if mode == "detection_mode":
        results = model(source=frame, conf=0.80)
        output_frame = results[0].plot()

    elif mode == "heatmap_mode":
        results = heatmap(frame)
        output_frame = results.plot_im
    
    elif mode == "dashboard_mode":
        heat_dash = heatmap(frame).plot_im
        detect_dash = model(source=frame, conf=0.80)[0].plot()

        if heat_dash.shape != detect_dash.shape:
            heat_dash = cv2.resize(heat_dash, (detect_dash.shape[1], detect_dash.shape[0]))

        output_frame = np.hstack((heat_dash, detect_dash))
    
    end_time = time.time()
    fps = 1 / (end_time - start_time)
    output_frame = draw_fps(output_frame, fps)

    # Frame bytes
    return convert_frame2bytes(output_frame)

def generate_stream(mode):
    try:
        cap = cv2.VideoCapture(0)

        while True:
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
            frame_bytes = process_frame(frame, mode, start_time)

            if frame_bytes is None:
                continue
            
            # Usando mime-type
            yield (
                b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        cap.release()
