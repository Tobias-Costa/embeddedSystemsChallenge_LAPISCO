import cv2
from ultralytics import YOLO
from ultralytics.solutions import Heatmap
import numpy as np

model = YOLO("yolo_models/best.pt")
heatmap = Heatmap(show=False, model=model, colormap=cv2.COLORMAP_PARULA, conf=0.40)

def convert_frame2bytes(frame):
    sucess, buffer = cv2.imencode(".jpg", frame)

    if not sucess:
        print("Error: Couldn't transform frame to '.jpg' buffer")
        return None

    return buffer.tobytes()

def process_frame(frame, mode):

    if mode == "detection_mode":
        results = model(source=frame, conf=0.40)
        # Frame bytes
        return convert_frame2bytes(results[0].plot())

    if mode == "heatmap_mode":
        results = heatmap(frame)
        # Frame bytes
        return convert_frame2bytes(results.plot_im)
    
    if mode == "dashboard_mode":
        heat_dash = heatmap(frame).plot_im
        detect_dash = model(source=frame, conf=0.40)[0].plot()

        if heat_dash.shape != detect_dash.shape:
            heat_dash = cv2.resize(heat_dash, (detect_dash[1], detect_dash[0]))

        combined_frame = np.hstack((heat_dash, detect_dash))
        
        # Frame bytes
        return convert_frame2bytes(combined_frame)

def generate_stream(mode):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Não foi possível acessar a câmera.")
        return 0

    while cap.isOpened():
        sucess, frame = cap.read()

        if not sucess:
            print("Erro de processamento.")
            break

        frame_bytes = process_frame(frame, mode)

        # Usando mime-type
        yield (
            b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )

    cap.release()

# UNUSED CODE

# def detection_person_boxes_generator():
#     model = setup_model()
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         print("Não foi possível acessar a câmera.")
#         return 0

#     while cap.isOpened():
#         sucess, frame = cap.read()

#         if not sucess:
#             print("Erro de processamento.")
#             break

        # results = model(source=frame, conf=0.20, verbose=False)

        # frame_bytes = convert_frame2bytes(results[0].plot())
#         # Usando mime-type
#         yield (
#             b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
#         )

#     cap.release()


# def person_heatmap_generator():
#     model = setup_model()
#     heatmap = Heatmap(show=False, model=model, colormap=cv2.COLORMAP_PARULA, conf=0.20)
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         print("Não foi possível acessar a câmera.")
#         return 0

#     while cap.isOpened():
#         sucess, frame = cap.read()

#         if not sucess:
#             print("Erro de processamento.")
#             break

#         results = heatmap(frame)

#         frame_bytes = convert_frame2bytes(results.plot_im)
#         # Usando mime-type
#         yield (
#             b"--frame\r\n" b"content-type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
#         )

#     cap.release()
