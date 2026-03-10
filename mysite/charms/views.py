from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from MonsterHunterWorld.models import Charm


def charms_index(request):
    q = request.GET.get('q', '').strip()
    rarity_filter = request.GET.get('rarity', '')

    charms_qs = Charm.objects.prefetch_related('charm_skills__skill').all().order_by('rarity', 'name')

    if q:
        charms_qs = charms_qs.filter(name__icontains=q)
    if rarity_filter:
        charms_qs = charms_qs.filter(rarity=rarity_filter)

    rarities = Charm.objects.values_list('rarity', flat=True).distinct().order_by('rarity')

    try:
        page_size = int(request.GET.get("page_size", 15))
    except (TypeError, ValueError):
        page_size = 15
    if page_size not in (10, 15, 20):
        page_size = 15

    paginator = Paginator(charms_qs, page_size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = {'page_size': page_size}
    if q:
        params['q'] = q
    if rarity_filter:
        params['rarity'] = rarity_filter
    filter_qs = urlencode(params)

    return render(request, 'charms.html', {
        'charms': page_obj.object_list,
        'page_obj': page_obj,
        'page_size': page_size,
        'q': q,
        'rarity_filter': rarity_filter,
        'rarities': rarities,
        'filter_qs': filter_qs,
    })
