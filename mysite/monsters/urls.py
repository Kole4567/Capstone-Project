from django.urls import path
from . import views

urlpatterns = [
    path('', views.monsters_index, name='monsters_index'), # This leads to /monsters
    path('monster/<int:monster_id>/build/', views.monster_detail, name='monster_build'),
    path('monster/<int:pk>/slay/', views.slay_monster, name='slay_monster'),
    path('monster/<int:pk>/unslay/', views.unslay_monster, name='unslay_monster'),
]