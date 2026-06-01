from django.urls import path
from . import views

urlpatterns = [
    path("detection/", views.dashboard, name="dashboard"),
    path("api/", views.camera_api, name="camera_api"),
]
