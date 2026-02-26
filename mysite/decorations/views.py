from django.shortcuts import render
from MonsterHunterWorld.models import Decoration

# Create your views here.
def decorations_index(request):
    # Prefetch skills to avoid N+1 query issues
    decorations = Decoration.objects.prefetch_related('decoration_skills__skill').all().order_by('-rarity', 'name')
    
    return render(request, 'decorations.html', {
        'decorations': decorations
    })