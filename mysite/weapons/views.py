from django.shortcuts import render
from MonsterHunterWorld.models import Weapon
from inventory.models import WeaponInventory


def weapon_index(request):
    weapons = Weapon.objects.all().order_by('rarity', 'name')

    can_manage_inventory = request.user.is_authenticated
    owned_weapon_ids = set()

    if can_manage_inventory:
        owned_weapon_ids = set(
            WeaponInventory.objects.filter(user=request.user)
            .values_list("weapon_id", flat=True)
        )

    return render(
        request,
        "weapons.html",
        {
            "weapons": weapons,
            "can_manage_inventory": can_manage_inventory,
            "owned_weapon_ids": owned_weapon_ids,
        }
    )