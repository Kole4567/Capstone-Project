from django.db import models
from django.contrib.auth.models import User


class CommunityPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=300)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.ManyToManyField(User, blank=True, related_name='community_upvotes')

    def upvote_count(self):
        return self.upvotes.count()

    def comment_count(self):
        return self.community_comments.count()

    def __str__(self):
        return f"{self.user.username} — {self.title}"


class CommunityComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='community_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on '{self.post.title}'"
