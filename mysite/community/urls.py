from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='community_feed'),
    path('create/', views.create, name='community_create'),
    path('<int:pk>/', views.detail, name='community_detail'),
    path('mine/', views.my_posts, name='my_posts_community'),
    path('<int:pk>/delete/', views.post_delete, name='community_post_delete'),
    path('<int:pk>/upvote/', views.upvote, name='community_upvote'),
    path('<int:pk>/comment/', views.comment, name='community_comment'),
]
