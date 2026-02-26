from django.urls import path
from . import views

urlpatterns = [
    path('', views.decorations_index, name='decorations_index'), # This leads to /decorations/
]