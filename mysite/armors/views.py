from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from MonsterHunterWorld.models import Armor
from inventory.models import ArmorInventory


def armors_index(request):
    q = request.GET.get('q', '').strip()
    armor_type = request.GET.get('armor_type', '')
    rarity_filter = request.GET.get('rarity', '')
    rank_filter = request.GET.get('rank', '')

    armors_qs = Armor.objects.prefetch_related('armor_skills__skill').all().order_by('-rarity', 'armor_set_name')

    if q:
        armors_qs = armors_qs.filter(name__icontains=q)
    if armor_type:
        armors_qs = armors_qs.filter(armor_type=armor_type)
    if rarity_filter:
        armors_qs = armors_qs.filter(rarity=rarity_filter)
    if rank_filter:
        armors_qs = armors_qs.filter(armor_set_rank=rank_filter)

    armor_types = Armor.objects.values_list('armor_type', flat=True).distinct().order_by('armor_type')
    rarities = Armor.objects.values_list('rarity', flat=True).distinct().order_by('rarity')
    ranks = Armor.objects.values_list('armor_set_rank', flat=True).distinct().order_by('armor_set_rank')

    owned_armor_ids = set()
    if request.user.is_authenticated:
        owned_armor_ids = set(
            ArmorInventory.objects.filter(user=request.user).values_list('armor_id', flat=True)
        )

    try:
        page_size = int(request.GET.get("page_size", 15))
    except (TypeError, ValueError):
        page_size = 15
    if page_size not in (10, 15, 20):
        page_size = 15

    paginator = Paginator(armors_qs, page_size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    params = {'page_size': page_size}
    if q:
        params['q'] = q
    if armor_type:
        params['armor_type'] = armor_type
    if rarity_filter:
        params['rarity'] = rarity_filter
    if rank_filter:
        params['rank'] = rank_filter
    filter_qs = urlencode(params)

    return render(request, 'armors.html', {
        'armors': page_obj.object_list,
        'page_obj': page_obj,
        'page_size': page_size,
        'q': q,
        'armor_type': armor_type,
        'rarity_filter': rarity_filter,
        'rank_filter': rank_filter,
        'armor_types': armor_types,
        'rarities': rarities,
        'ranks': ranks,
        'filter_qs': filter_qs,
        'owned_armor_ids': owned_armor_ids,
    })
