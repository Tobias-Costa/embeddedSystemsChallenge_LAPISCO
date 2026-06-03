from django.urls import path
from . import views

# Rotas do app 'person_detection_app'
urlpatterns = [
    path("detection/", views.dashboard, name="dashboard"),
    path("api/", views.camera_api, name="camera_api"),
]
