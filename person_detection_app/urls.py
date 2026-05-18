from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('person/detection/', views.detection, name='detection'),
    path('person/heatmap/', views.heatmap, name='heatmap'),
]