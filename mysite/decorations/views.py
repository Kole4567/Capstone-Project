from django.shortcuts import render
from MonsterHunterWorld.models import Decoration
from inventory.models import DecorationInventory

def decorations_index(request):
    decorations = Decoration.objects.prefetch_related('decoration_skills__skill').all().order_by('-rarity', 'name')
    
    owned_decoration_ids = set()
    if request.user.is_authenticated:
        owned_decoration_ids = set(
            DecorationInventory.objects.filter(user=request.user).values_list('decoration_id', flat=True)
        )
    
    return render(request, 'decorations.html', {
        'decorations': decorations,
        'owned_decoration_ids': owned_decoration_ids,
    })