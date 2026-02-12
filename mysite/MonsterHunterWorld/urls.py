from django.urls import path

from . import views

urlpatterns = [  
    # This will now be the main page at 127.0.0.1:8000/
    path("", views.home, name="home"), 
]
