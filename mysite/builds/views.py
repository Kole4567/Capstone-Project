from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from MonsterHunterWorld.models import Weapon, Armor, Charm, Decoration
from .models import SavedBuild, BuildLike, BuildComment


def feed(request):
    builds = SavedBuild.objects.filter(is_public=True).select_related(
        'user', 'weapon'
    ).prefetch_related('likes', 'comments').order_by('-created_at')

    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(BuildLike.objects.filter(user=request.user).values_list('build_id', flat=True))

    return render(request, 'builds/feed.html', {
        'builds': builds,
        'liked_ids': liked_ids,
    })


@login_required
def create(request):
    if request.method == 'POST':
        build = SavedBuild.objects.create(
            user=request.user,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            weapon=Weapon.objects.filter(pk=request.POST.get('weapon')).first(),
            head=Armor.objects.filter(pk=request.POST.get('head')).first(),
            chest=Armor.objects.filter(pk=request.POST.get('chest')).first(),
            arms=Armor.objects.filter(pk=request.POST.get('arms')).first(),
            waist=Armor.objects.filter(pk=request.POST.get('waist')).first(),
            legs=Armor.objects.filter(pk=request.POST.get('legs')).first(),
            charm=Charm.objects.filter(pk=request.POST.get('charm')).first(),
            is_public=request.POST.get('is_public') == 'on',
        )
        deco_ids = request.POST.getlist('decorations')
        if deco_ids:
            build.decorations.set(Decoration.objects.filter(pk__in=deco_ids))
        return redirect('build_detail', pk=build.pk)

    return render(request, 'builds/create.html', {
        'weapons': Weapon.objects.order_by('name'),
        'slot_data': [
            ('head',  'Head',  Armor.objects.filter(armor_type='head').order_by('name')),
            ('chest', 'Chest', Armor.objects.filter(armor_type='chest').order_by('name')),
            ('arms',  'Arms',  Armor.objects.filter(armor_type='gloves').order_by('name')),
            ('waist', 'Waist', Armor.objects.filter(armor_type='waist').order_by('name')),
            ('legs',  'Legs',  Armor.objects.filter(armor_type='legs').order_by('name')),
        ],
        'charms': Charm.objects.order_by('name'),
        'decorations': Decoration.objects.order_by('name'),
    })


def detail(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk)
    if not build.is_public and build.user != request.user:
        return redirect('builds_feed')

    liked = False
    if request.user.is_authenticated:
        liked = BuildLike.objects.filter(user=request.user, build=build).exists()

    comments = build.comments.select_related('user').order_by('created_at')

    return render(request, 'builds/detail.html', {
        'build': build,
        'liked': liked,
        'comments': comments,
    })


@login_required
def edit(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk, user=request.user)

    if request.method == 'POST':
        build.title = request.POST.get('title', '').strip()
        build.description = request.POST.get('description', '').strip()
        build.weapon = Weapon.objects.filter(pk=request.POST.get('weapon')).first()
        build.head = Armor.objects.filter(pk=request.POST.get('head')).first()
        build.chest = Armor.objects.filter(pk=request.POST.get('chest')).first()
        build.arms = Armor.objects.filter(pk=request.POST.get('arms')).first()
        build.waist = Armor.objects.filter(pk=request.POST.get('waist')).first()
        build.legs = Armor.objects.filter(pk=request.POST.get('legs')).first()
        build.charm = Charm.objects.filter(pk=request.POST.get('charm')).first()
        build.is_public = request.POST.get('is_public') == 'on'
        build.save()
        deco_ids = request.POST.getlist('decorations')
        build.decorations.set(Decoration.objects.filter(pk__in=deco_ids) if deco_ids else [])
        return redirect('build_detail', pk=build.pk)

    return render(request, 'builds/edit.html', {
        'build': build,
        'weapons': Weapon.objects.order_by('name'),
        'slot_data': [
            ('head',  'Head',  Armor.objects.filter(armor_type='head').order_by('name')),
            ('chest', 'Chest', Armor.objects.filter(armor_type='chest').order_by('name')),
            ('arms',  'Arms',  Armor.objects.filter(armor_type='gloves').order_by('name')),
            ('waist', 'Waist', Armor.objects.filter(armor_type='waist').order_by('name')),
            ('legs',  'Legs',  Armor.objects.filter(armor_type='legs').order_by('name')),
        ],
        'charms': Charm.objects.order_by('name'),
        'decorations': Decoration.objects.order_by('name'),
    })


@login_required
@require_POST
def delete(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk, user=request.user)
    build.delete()
    return redirect('my_builds')


@login_required
@require_POST
def like(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk)
    obj, created = BuildLike.objects.get_or_create(user=request.user, build=build)
    if not created:
        obj.delete()
    return JsonResponse({'liked': created, 'count': build.like_count()})


@login_required
@require_POST
def comment(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk)
    text = request.POST.get('text', '').strip()
    if text:
        c = BuildComment.objects.create(user=request.user, build=build, text=text)
        return JsonResponse({
            'username': c.user.username,
            'text': c.text,
            'created_at': c.created_at.strftime('%b %d, %Y'),
        })
    return JsonResponse({'error': 'Empty comment'}, status=400)


@login_required
def my_builds(request):
    builds = SavedBuild.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'builds/my_builds.html', {'builds': builds})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    builds = SavedBuild.objects.filter(user=profile_user, is_public=True).order_by('-created_at')
    return render(request, 'builds/profile.html', {
        'profile_user': profile_user,
        'builds': builds,
    })
