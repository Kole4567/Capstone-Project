from django.shortcuts import render
from MonsterHunterWorld.models import Charm

# This name MUST match what is in your weapons/urls.py
def charms_index(request):
    # Fetch all weapons stored in YOUR internal database
    # This uses your stable API contracts instead of the mhw-db structure
    charms = Charm.objects.prefetch_related('charm_skills__skill').all().order_by('rarity', 'name')
    
    return render(request, 'charms.html', {
        'charms': charms
    })