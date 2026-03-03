from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_home, name='inventory_home'),
    path('add/weapon/<int:pk>/', views.add_weapon, name='add_weapon'),
    path("remove/weapon/<int:pk>/", views.remove_weapon, name="remove_weapon"),
    path('add/armor/<int:pk>/', views.add_armor, name='add_armor'),
    path('add/charm/<int:pk>/', views.add_charm, name='add_charm'),
    path('add/decoration/<int:pk>/', views.add_decoration, name='add_decoration'),
]