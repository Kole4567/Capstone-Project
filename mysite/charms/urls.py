from django.urls import path
from . import views

urlpatterns = [
    path('', views.charms_index, name='charms_index'), # This leads to /charms
]