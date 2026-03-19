from django.db import models
from django.contrib.auth.models import User
from MonsterHunterWorld.models import Weapon, Armor, Charm, Decoration


class SavedBuild(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_builds')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    weapon = models.ForeignKey(Weapon, on_delete=models.SET_NULL, null=True, blank=True)
    head = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_head')
    chest = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_chest')
    arms = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_arms')
    waist = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_waist')
    legs = models.ForeignKey(Armor, on_delete=models.SET_NULL, null=True, blank=True, related_name='build_legs')
    charm = models.ForeignKey(Charm, on_delete=models.SET_NULL, null=True, blank=True)
    decorations = models.ManyToManyField(Decoration, blank=True)

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    def __str__(self):
        return f"{self.user.username} — {self.title}"


class BuildLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    build = models.ForeignKey(SavedBuild, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'build')


class BuildComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    build = models.ForeignKey(SavedBuild, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on '{self.build.title}'"
