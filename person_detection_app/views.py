from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from . import camera

# Create your views here.


def index(request):
    return render(request, "index.html")


def detection(request):
    return render(request, "person_detection.html")


def heatmap(request):
    return render(request, "person_heatmap.html")


def dashboard(request):
    return render(request, "dashboard.html")


def camera_api(request, mode):
    return StreamingHttpResponse(
        camera.generate_stream(mode),
        content_type="multipart/x-mixed-replace;boundary=frame",
    )


# def heatmap_api(request, mode):
#     return StreamingHttpResponse(
#         camera.generate_stream(mode),
#         content_type="multipart/x-mixed-replace;boundary=frame",
#     )
