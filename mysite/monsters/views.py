from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from MonsterHunterWorld.models import Monster
from MonsterHunterWorld.build_logic import best_build_fast


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

    try:
        page_size = int(request.GET.get("page_size", 15))
    except (TypeError, ValueError):
        page_size = 15
    if page_size not in (10, 15, 20):
        page_size = 15

    paginator = Paginator(monsters_qs, page_size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = {'page_size': page_size}
    if q:
        params['q'] = q
    if monster_type:
        params['monster_type'] = monster_type
    if elder_filter:
        params['elder'] = elder_filter
    filter_qs = urlencode(params)

    return render(request, 'monsters.html', {
        'monsters': page_obj.object_list,
        'page_obj': page_obj,
        'page_size': page_size,
        'q': q,
        'monster_type': monster_type,
        'elder_filter': elder_filter,
        'monster_types': monster_types,
        'filter_qs': filter_qs,
    })


def monster_detail(request, monster_id):
    monster = Monster.objects.get(id=monster_id)
    recommendation = best_build_fast(monster)
    return render(request, 'build_recommendation.html', {
        'monster': monster,
        'build': recommendation
    })
