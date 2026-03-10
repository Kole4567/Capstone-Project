from django.db import models
from django.contrib.auth.models import User
from MonsterHunterWorld.models import Monster

# Create your models here.
class SlayedMonster(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slayed_monsters')
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)
    slayed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'monster'], name='uniq_slayed_monster_user_monster')
        ]

    def __str__(self):
        return f"{self.user.username} slayed {self.monster.name}"