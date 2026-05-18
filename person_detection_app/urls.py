from django.urls import path
from . import views

urlpatterns = [
    path('detection/', views.detection, name='detection'),
    path('detection/heatmap', views.detection_heatmap, name='detection_heatmap'),
]