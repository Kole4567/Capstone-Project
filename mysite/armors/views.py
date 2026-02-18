from django.shortcuts import render
from MonsterHunterWorld.models import Armor

# This name MUST match what is in your weapons/urls.py
def armors_index(request):
    # Fetch all weapons stored in YOUR internal database
    # This uses your stable API contracts instead of the mhw-db structure
    armors = Armor.objects.prefetch_related('armor_skills__skill').all().order_by('rarity')
    
    return render(request, 'armors.html', {
        'armors': armors
    })