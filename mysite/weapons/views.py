from django.shortcuts import render
from django.core.paginator import Paginator
from urllib.parse import urlencode
from MonsterHunterWorld.models import Weapon
from inventory.models import WeaponInventory


def weapon_index(request):
    q = request.GET.get('q', '').strip()
    weapon_type = request.GET.get('weapon_type', '')
    element_filter = request.GET.get('element', '')
    rarity_filter = request.GET.get('rarity', '')

    weapons_qs = Weapon.objects.all().order_by("rarity", "name")

    if q:
        weapons_qs = weapons_qs.filter(name__icontains=q)
    if weapon_type:
        weapons_qs = weapons_qs.filter(weapon_type=weapon_type)
    if element_filter == 'none':
        weapons_qs = weapons_qs.filter(element__isnull=True) | weapons_qs.filter(element='')
    elif element_filter:
        weapons_qs = weapons_qs.filter(element__iexact=element_filter)
    if rarity_filter:
        weapons_qs = weapons_qs.filter(rarity=rarity_filter)

    weapon_types = Weapon.objects.values_list('weapon_type', flat=True).distinct().order_by('weapon_type')
    elements = (
        Weapon.objects
        .exclude(element__isnull=True).exclude(element='')
        .values_list('element', flat=True).distinct().order_by('element')
    )
    rarities = Weapon.objects.values_list('rarity', flat=True).distinct().order_by('rarity')

    try:
        page_size = int(request.GET.get("page_size", 15))
    except (TypeError, ValueError):
        page_size = 15
    if page_size not in (10, 15, 20):
        page_size = 15

    paginator = Paginator(weapons_qs, page_size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    can_manage_inventory = request.user.is_authenticated
    owned_weapon_ids = set()

    if can_manage_inventory:
        current_page_weapon_ids = [w.id for w in page_obj.object_list]
        owned_weapon_ids = set(
            WeaponInventory.objects.filter(
                user=request.user,
                weapon_id__in=current_page_weapon_ids
            ).values_list("weapon_id", flat=True)
        )

    params = {'page_size': page_size}
    if q:
        params['q'] = q
    if weapon_type:
        params['weapon_type'] = weapon_type
    if element_filter:
        params['element'] = element_filter
    if rarity_filter:
        params['rarity'] = rarity_filter
    filter_qs = urlencode(params)

    return render(request, "weapons.html", {
        "weapons": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "page_size": page_size,
        "can_manage_inventory": can_manage_inventory,
        "owned_weapon_ids": owned_weapon_ids,
        "q": q,
        "weapon_type": weapon_type,
        "element_filter": element_filter,
        "rarity_filter": rarity_filter,
        "weapon_types": weapon_types,
        "elements": elements,
        "rarities": rarities,
        "filter_qs": filter_qs,
    })
