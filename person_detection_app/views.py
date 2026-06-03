from django.shortcuts import render
from django.http import StreamingHttpResponse
from camera import generate_stream

# Create your views here.

# View de dashboard com header e imagens da stream
def dashboard(request):
    return render(request, "dashboard.html")

# Rota API que retorna um MJPEG contínuo
def camera_api(request):
    return StreamingHttpResponse(
        generate_stream(),
        content_type="multipart/x-mixed-replace;boundary=frame",
    )