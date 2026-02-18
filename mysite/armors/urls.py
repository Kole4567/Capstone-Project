from django.urls import path
from . import views

urlpatterns = [
    path('', views.armors_index, name='armors_index'), # This leads to /armors/
]