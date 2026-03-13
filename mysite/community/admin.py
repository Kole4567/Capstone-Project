from django.contrib import admin
from .models import CommunityPost, CommunityComment

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'upvote_count', 'comment_count')
    search_fields = ('title', 'user__username')
    ordering = ('-created_at',)

@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    search_fields = ('post__title', 'user__username')
    ordering = ('-created_at',)
