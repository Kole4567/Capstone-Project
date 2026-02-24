from django.shortcuts import render
from MonsterHunterWorld.models import Charm

def charms_index(request):
    # Fetch all weapons stored in internal database
    charms = Charm.objects.prefetch_related('charm_skills__skill').all().order_by('rarity', 'name')
    
    return render(request, 'charms.html', {
        'charms': charms
    })