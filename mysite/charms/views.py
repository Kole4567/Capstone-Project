from django.shortcuts import render
from MonsterHunterWorld.models import Charm
from inventory.models import CharmInventory

def charms_index(request):
    charms = Charm.objects.prefetch_related('charm_skills__skill').all().order_by('rarity', 'name')
    
    owned_charm_ids = set()
    if request.user.is_authenticated:
        owned_charm_ids = set(
            CharmInventory.objects.filter(user=request.user).values_list('charm_id', flat=True)
        )
    
    return render(request, 'charms.html', {
        'charms': charms,
        'owned_charm_ids': owned_charm_ids,
    })