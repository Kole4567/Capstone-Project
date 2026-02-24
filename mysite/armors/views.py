from django.shortcuts import render
from MonsterHunterWorld.models import Armor

def armors_index(request):
    # Fetch all weapons stored in internal database
    armors = Armor.objects.prefetch_related('armor_skills__skill').all().order_by('-rarity', 'armor_set_name')
    
    return render(request, 'armors.html', {
        'armors': armors
    })