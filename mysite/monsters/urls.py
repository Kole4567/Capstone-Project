from django.urls import path
from . import views

urlpatterns = [
    path('', views.monsters_index, name='monsters_index'), # This leads to /monsters
]