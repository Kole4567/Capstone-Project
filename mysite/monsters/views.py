from django.shortcuts import render
from MonsterHunterWorld.models import Monster

# This name MUST match what is in your weapons/urls.py
def monsters_index(request):
    # Fetch all weapons stored in YOUR internal database
    # This uses your stable API contracts instead of the mhw-db structure
    monsters = Monster.objects.all().order_by('name')
    
    return render(request, 'monsters.html', {
        'monsters': monsters
    })