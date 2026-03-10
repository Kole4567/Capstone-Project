from django.shortcuts import render
from MonsterHunterWorld.models import Armor
from inventory.models import ArmorInventory

def armors_index(request):
    armors = Armor.objects.prefetch_related('armor_skills__skill').all().order_by('-rarity', 'armor_set_name')
    
    owned_armor_ids = set()
    if request.user.is_authenticated:
        owned_armor_ids = set(
            ArmorInventory.objects.filter(user=request.user).values_list('armor_id', flat=True)
        )

    return render(request, 'armors.html', {
        'armors': armors,
        'owned_armor_ids': owned_armor_ids,
    })