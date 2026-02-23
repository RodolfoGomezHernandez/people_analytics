from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dotacion_index'),
]