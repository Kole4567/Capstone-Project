from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from MonsterHunterWorld.models import Decoration
from inventory.models import DecorationInventory


def decorations_index(request):
    q = request.GET.get('q', '').strip()
    rarity_filter = request.GET.get('rarity', '')

    decos_qs = Decoration.objects.prefetch_related('decoration_skills__skill').all().order_by('-rarity', 'name')

    if q:
        decos_qs = decos_qs.filter(name__icontains=q)
    if rarity_filter:
        decos_qs = decos_qs.filter(rarity=rarity_filter)

    rarities = Decoration.objects.values_list('rarity', flat=True).distinct().order_by('rarity')

    owned_decoration_ids = set()
    if request.user.is_authenticated:
        owned_decoration_ids = set(
            DecorationInventory.objects.filter(user=request.user).values_list('decoration_id', flat=True)
        )

    paginator = Paginator(decos_qs, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = {}
    if q: params['q'] = q
    if rarity_filter: params['rarity'] = rarity_filter
    filter_qs = urlencode(params)

    cur = page_obj.number
    total = page_obj.paginator.num_pages
    page_range = list(range(max(1, cur - 1), min(total, cur + 1) + 1))

    return render(request, 'decorations.html', {
        'decorations': page_obj.object_list,
        'page_obj': page_obj,
        'q': q,
        'rarity_filter': rarity_filter,
        'rarities': rarities,
        'filter_qs': filter_qs,
        'owned_decoration_ids': owned_decoration_ids,
        'page_range': page_range,
    })
