from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from MonsterHunterWorld.models import Weapon, Armor, Charm, Decoration
from .models import (
    WeaponInventory,
    ArmorInventory,
    CharmInventory,
    DecorationInventory,
)

# ==================================================
# Inventory Home Page
# ==================================================

@login_required
def inventory_home(request):
    weapons = WeaponInventory.objects.filter(user=request.user).select_related("weapon")
    armors = ArmorInventory.objects.filter(user=request.user).select_related("armor")
    charms = CharmInventory.objects.filter(user=request.user).select_related("charm")
    decorations = DecorationInventory.objects.filter(user=request.user).select_related("decoration")

    return render(
        request,
        "inventory.html",
        {
            "weapons": weapons,
            "armors": armors,
            "charms": charms,
            "decorations": decorations,
        },
    )


# ==================================================
# Add Items to Inventory (POST only)
# ==================================================

@login_required
@require_POST
def add_weapon(request, pk):
    weapon = get_object_or_404(Weapon, pk=pk)
    obj, created = WeaponInventory.objects.get_or_create(
        user=request.user,
        weapon=weapon,
    )
    return JsonResponse({
        "added": created,
        "message": "Weapon added!" if created else "Weapon already owned",
    })

@login_required
@require_POST
def remove_weapon(request, pk):
    weapon = get_object_or_404(Weapon, pk=pk)

    deleted, _ = WeaponInventory.objects.filter(
        user=request.user,
        weapon=weapon,
    ).delete()

    return JsonResponse({
        "removed": deleted > 0,
        "message": "Weapon removed!" if deleted else "Weapon not in inventory",
    })


@login_required
@require_POST
def add_armor(request, pk):
    armor = get_object_or_404(Armor, pk=pk)
    obj, created = ArmorInventory.objects.get_or_create(
        user=request.user,
        armor=armor,
    )
    return JsonResponse({
        "added": created,
        "message": "Armor added!" if created else "Armor already owned",
    })

@login_required
@require_POST
def remove_armor(request, pk):
    armor = get_object_or_404(Armor, pk=pk)
    deleted, _ = ArmorInventory.objects.filter(
        user=request.user,
        armor=armor,
    ).delete()
    return JsonResponse({
        "removed": deleted > 0,
        "message": "Armor removed!" if deleted else "Armor not in inventory",
    })

@login_required
@require_POST
def add_charm(request, pk):
    charm = get_object_or_404(Charm, pk=pk)
    obj, created = CharmInventory.objects.get_or_create(
        user=request.user,
        charm=charm,
    )
    return JsonResponse({
        "added": created,
        "message": "Charm added!" if created else "Charm already owned",
    })

@login_required
@require_POST
def remove_charm(request, pk):
    charm = get_object_or_404(Charm, pk=pk)
    deleted, _ = CharmInventory.objects.filter(
        user=request.user,
        charm=charm,
    ).delete()
    return JsonResponse({
        "removed": deleted > 0,
        "message": "Charm removed!" if deleted else "Charm not in inventory",
    })

@login_required
@require_POST
def add_decoration(request, pk):
    decoration = get_object_or_404(Decoration, pk=pk)

    obj, created = DecorationInventory.objects.get_or_create(
        user=request.user,
        decoration=decoration,
        defaults={"quantity": 1},
    )

    if not created:
        obj.quantity += 1
        obj.save(update_fields=["quantity"])

    return JsonResponse({
        "added": True,
        "quantity": obj.quantity,
        "message": "Decoration added",
    })

@login_required
@require_POST
def reset_inventory(request):
    WeaponInventory.objects.filter(user=request.user).delete()
    ArmorInventory.objects.filter(user=request.user).delete()
    CharmInventory.objects.filter(user=request.user).delete()
    DecorationInventory.objects.filter(user=request.user).delete()
    return redirect('inventory_home')

@login_required
@require_POST
def remove_decoration(request, pk):
    decoration = get_object_or_404(Decoration, pk=pk)
    obj = DecorationInventory.objects.filter(
        user=request.user,
        decoration=decoration,
    ).first()

    if not obj:
        return JsonResponse({"removed": False, "message": "Decoration not in inventory"})

    if obj.quantity > 1:
        obj.quantity -= 1
        obj.save(update_fields=["quantity"])
        return JsonResponse({"removed": True, "quantity": obj.quantity, "message": "Decoration quantity reduced"})
    else:
        obj.delete()
        return JsonResponse({"removed": True, "quantity": 0, "message": "Decoration removed!"})