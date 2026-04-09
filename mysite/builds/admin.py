from django.contrib import admin
from .models import SavedBuild, BuildLike, BuildComment, BuildReport, BuildCommentReport


@admin.register(SavedBuild)
class SavedBuildAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'created_at')
    search_fields = ('title', 'user__username')
    ordering = ('-created_at',)


@admin.register(BuildComment)
class BuildCommentAdmin(admin.ModelAdmin):
    list_display = ('build', 'user', 'created_at')
    search_fields = ('build__title', 'user__username')
    ordering = ('-created_at',)


@admin.register(BuildReport)
class BuildReportAdmin(admin.ModelAdmin):
    list_display = ('build', 'user', 'reason', 'created_at')
    search_fields = ('build__title', 'user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'build', 'reason', 'created_at')


@admin.register(BuildCommentReport)
class BuildCommentReportAdmin(admin.ModelAdmin):
    list_display = ('comment', 'user', 'reason', 'created_at')
    search_fields = ('comment__text', 'user__username', 'reason')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'comment', 'reason', 'created_at')
