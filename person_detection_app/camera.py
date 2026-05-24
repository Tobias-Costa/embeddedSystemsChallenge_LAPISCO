import cv2
from ultralytics import YOLO
from ultralytics.solutions import Heatmap
import numpy as np

model = YOLO("yolo_models/yolo26n_openvino_model")

heatmap = Heatmap(show=False, model=model, colormap=cv2.COLORMAP_PARULA, conf=0.40)

def convert_frame2bytes(frame):
    success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        print("Error: Couldn't transform frame to '.jpg' buffer")
        return None

    return buffer.tobytes()

def process_frame(frame, mode):

    if mode == "detection_mode":
        results = model(source=frame, conf=0.80)
        # Frame bytes
        return convert_frame2bytes(results[0].plot())

    elif mode == "heatmap_mode":
        results = heatmap(frame)
        # Frame bytes
        return convert_frame2bytes(results.plot_im)
    
    elif mode == "dashboard_mode":
        heat_dash = heatmap(frame).plot_im
        detect_dash = model(source=frame, conf=0.80)[0].plot()

        if heat_dash.shape != detect_dash.shape:
            heat_dash = cv2.resize(heat_dash, (detect_dash.shape[1], detect_dash.shape[0]))

        combined_frame = np.hstack((heat_dash, detect_dash))
        
        # Frame bytes
        return convert_frame2bytes(combined_frame)

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

            frame_bytes = process_frame(frame, mode)

            if frame_bytes is None:
                continue

            # Usando mime-type
            yield (
                b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    finally:
        cap.release()
