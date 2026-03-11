from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from MonsterHunterWorld.models import Monster
from MonsterHunterWorld.build_logic import best_build_fast
from monsters.models import SlayedMonster


def monsters_index(request):
    q = request.GET.get('q', '').strip()
    monster_type = request.GET.get('monster_type', '')
    elder_filter = request.GET.get('elder', '')

    monsters_qs = Monster.objects.all().order_by('name')

    if q:
        monsters_qs = monsters_qs.filter(name__icontains=q)
    if monster_type:
        monsters_qs = monsters_qs.filter(monster_type=monster_type)
    if elder_filter == 'yes':
        monsters_qs = monsters_qs.filter(is_elder_dragon=True)
    elif elder_filter == 'no':
        monsters_qs = monsters_qs.filter(is_elder_dragon=False)

    monster_types = Monster.objects.values_list('monster_type', flat=True).distinct().order_by('monster_type')

    slayed_monster_ids = set()
    if request.user.is_authenticated:
        slayed_monster_ids = set(
            SlayedMonster.objects.filter(user=request.user).values_list('monster_id', flat=True)
        )

    paginator = Paginator(monsters_qs, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = {}
    if q: params['q'] = q
    if monster_type: params['monster_type'] = monster_type
    if elder_filter: params['elder'] = elder_filter
    filter_qs = urlencode(params)

    cur = page_obj.number
    total = page_obj.paginator.num_pages
    page_range = list(range(max(1, cur - 1), min(total, cur + 1) + 1))

    return render(request, 'monsters.html', {
        'monsters': page_obj.object_list,
        'page_obj': page_obj,
        'q': q,
        'monster_type': monster_type,
        'elder_filter': elder_filter,
        'monster_types': monster_types,
        'filter_qs': filter_qs,
        'slayed_monster_ids': slayed_monster_ids,
        'page_range': page_range,
    })


def monster_detail(request, monster_id):
    monster = Monster.objects.get(id=monster_id)
    recommendation = best_build_fast(monster)
    return render(request, 'build_recommendation.html', {
        'monster': monster,
        'build': recommendation
    })


@login_required
def my_hunts(request):
    slayed = SlayedMonster.objects.filter(user=request.user).select_related('monster').order_by('monster__name')
    total_count = Monster.objects.count()
    slayed_count = slayed.count()
    return render(request, 'my_hunts.html', {
        'slayed': slayed,
        'slayed_count': slayed_count,
        'total_count': total_count,
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
