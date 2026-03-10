from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from MonsterHunterWorld.models import Monster
from MonsterHunterWorld.build_logic import best_build_fast
from monsters.models import SlayedMonster

def monsters_index(request):
    monsters = Monster.objects.all().order_by('name')

    slayed_monster_ids = set()
    if request.user.is_authenticated:
        slayed_monster_ids = set(
            SlayedMonster.objects.filter(user=request.user).values_list('monster_id', flat=True)
        )

    return render(request, 'monsters.html', {
        'monsters': monsters,
        'slayed_monster_ids': slayed_monster_ids,
    })

def monster_detail(request, monster_id):
    monster = Monster.objects.get(id=monster_id)
    recommendation = best_build_fast(monster)

    return render(request, 'build_recommendation.html', {
        'monster': monster,
        'build': recommendation
    })

@login_required
@require_POST
def slay_monster(request, pk):
    monster = Monster.objects.get(pk=pk)
    obj, created = SlayedMonster.objects.get_or_create(user=request.user, monster=monster)
    return JsonResponse({'slayed': created, 'message': 'Monster slayed!' if created else 'Already slayed'})

@login_required
@require_POST
def unslay_monster(request, pk):
    monster = Monster.objects.get(pk=pk)
    deleted, _ = SlayedMonster.objects.filter(user=request.user, monster=monster).delete()
    return JsonResponse({'removed': deleted > 0, 'message': 'Slay undone!' if deleted else 'Not found'})