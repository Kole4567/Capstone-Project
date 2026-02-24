from django.shortcuts import render
from MonsterHunterWorld.models import Monster
from MonsterHunterWorld.build_logic import best_build_fast 

def monsters_index(request):
    # Fetch all weapons stored in internal database
    monsters = Monster.objects.all().order_by('name')
    
    return render(request, 'monsters.html', {
        'monsters': monsters
    })



def monster_detail(request, monster_id):
    monster = Monster.objects.get(id=monster_id)
    
    recommendation = best_build_fast(monster) 
    
    return render(request, 'build_recommendation.html', {
        'monster': monster,
        'build': recommendation
    })
