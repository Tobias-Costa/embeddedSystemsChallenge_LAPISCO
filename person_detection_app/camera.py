import cv2

def convert_frame2bytes(frame):
    sucess, buffer = cv2.imencode('.jpg', frame)

    if not sucess:
        print("Error: Couldn't transform frame to '.jpg' buffer")
        return None
    
    return buffer.tobytes()

def frames_generator():
    cap = cv2.VideoCapture(r"C:\Users\LABIC\Downloads\18790948-hd_1080_1920_30fps.mp4")

    if not cap.isOpened():
        print("Não foi possível ler o vídeo")
        return 0

    while cap.isOpened():
        sucess, frame = cap.read()

        if not sucess:
            print("Video frame is empty or processing is complete.")
            break

        frame_bytes = convert_frame2bytes(frame)
        # To do: implement content frame type
        yield frame_bytes 

    cap.release()

