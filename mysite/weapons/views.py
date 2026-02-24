from django.shortcuts import render
from MonsterHunterWorld.models import Weapon

def weapon_index(request):
    # Fetch all weapons stored in internal database
    weapons = Weapon.objects.all().order_by('rarity', 'name')
    
    return render(request, 'weapons.html', {
        'weapons': weapons
    })