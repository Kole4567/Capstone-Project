from django.db import models
from django.contrib.auth.models import User
from weapons.models import Weapon
from armors.models import Armor
from charms.models import Charm


class WeaponInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weapon_inventory')
    weapon = models.ForeignKey(Weapon, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'weapon'], name='uniq_weapon_inventory_user_weapon')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.weapon.name}"


class ArmorInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='armor_inventory')
    armor = models.ForeignKey(Armor, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'armor'], name='uniq_armor_inventory_user_armor')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.armor.name}"


class CharmInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='charm_inventory')
    charm = models.ForeignKey(Charm, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'charm'], name='uniq_charm_inventory_user_charm')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.charm.name}"