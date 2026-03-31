from django.contrib import admin
from .models import CommunityPost, CommunityComment, CommunityPostReport, CommunityCommentReport

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


@admin.register(CommunityPostReport)
class CommunityPostReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'reason', 'created_at')
    search_fields = ('post__title', 'user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'post', 'reason', 'created_at')


@admin.register(CommunityCommentReport)
class CommunityCommentReportAdmin(admin.ModelAdmin):
    list_display = ('comment', 'user', 'reason', 'created_at')
    search_fields = ('comment__body', 'user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'comment', 'reason', 'created_at')
