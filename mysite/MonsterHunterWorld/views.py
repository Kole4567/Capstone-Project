from django.shortcuts import render
from django.http import HttpResponse
from MonsterHunterWorld.models import Monster, Weapon


def home(request):
    monster_count = Monster.objects.count()
    weapon_count = Weapon.objects.count()
    return render(request, 'home.html', {
        'monster_count': monster_count,
        'weapon_count': weapon_count,
    })