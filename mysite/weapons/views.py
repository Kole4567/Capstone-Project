from django.shortcuts import render
from MonsterHunterWorld.models import Weapon

# This name MUST match what is in your weapons/urls.py
def weapon_index(request):
    # Fetch all weapons stored in YOUR internal database
    # This uses your stable API contracts instead of the mhw-db structure
    weapons = Weapon.objects.all().order_by('rarity', 'name')
    
    return render(request, 'weapons.html', {
        'weapons': weapons
    })