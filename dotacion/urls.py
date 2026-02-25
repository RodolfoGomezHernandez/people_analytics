from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dotacion_index'),
    path('api/kpis/', views.api_kpis, name='dotacion_api_kpis'),
]