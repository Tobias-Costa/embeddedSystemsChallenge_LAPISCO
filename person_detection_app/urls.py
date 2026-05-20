from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("person/detection/", views.detection, name="detection"),
    path("person/heatmap/", views.heatmap, name="heatmap"),
    path("person/dashboard/", views.dashboard, name="dashboard"),
    path("person/api/<str:mode>", views.camera_api, name="camera_api"),
]
