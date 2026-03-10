from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='builds_feed'),
    path('create/', views.create, name='build_create'),
    path('<int:pk>/', views.detail, name='build_detail'),
    path('<int:pk>/edit/', views.edit, name='build_edit'),
    path('<int:pk>/delete/', views.delete, name='build_delete'),
    path('<int:pk>/like/', views.like, name='build_like'),
    path('<int:pk>/comment/', views.comment, name='build_comment'),
    path('mine/', views.my_builds, name='my_builds'),
]
