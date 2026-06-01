from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from . import camera

# Create your views here.

def dashboard(request):
    return render(request, "dashboard.html")


def camera_api(request):
    return StreamingHttpResponse(
        camera.generate_stream(),
        content_type="multipart/x-mixed-replace;boundary=frame",
    )