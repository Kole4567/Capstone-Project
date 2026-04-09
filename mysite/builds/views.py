from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from MonsterHunterWorld.models import Weapon, Armor, Charm, Decoration
from .models import SavedBuild, BuildLike, BuildComment, BuildReport, BuildCommentReport


def feed(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'recent')

    builds = SavedBuild.objects.filter(is_public=True).select_related(
        'user', 'weapon'
    ).prefetch_related('likes', 'comments').annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True),
    )

    if q:
        builds = builds.filter(title__icontains=q) | builds.filter(description__icontains=q)

    if sort == 'upvotes':
        builds = builds.order_by('-likes_count', '-created_at')
    elif sort == 'comments':
        builds = builds.order_by('-comments_count', '-created_at')
    else:
        builds = builds.order_by('-created_at')

    paginator = Paginator(builds, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    cur = page_obj.number
    total = page_obj.paginator.num_pages
    page_range = list(range(max(1, cur - 1), min(total, cur + 1) + 1))

    filter_qs = ''
    if q:
        filter_qs += f'q={q}&'
    if sort and sort != 'recent':
        filter_qs += f'sort={sort}&'

    liked_ids = set()
    if request.user.is_authenticated:
        liked_ids = set(BuildLike.objects.filter(user=request.user).values_list('build_id', flat=True))

    return render(request, 'builds/feed.html', {
        'builds': page_obj,
        'page_obj': page_obj,
        'page_range': page_range,
        'filter_qs': filter_qs,
        'liked_ids': liked_ids,
        'q': q,
        'sort': sort,
    })


def _pk(post, key):
    val = post.get(key, '').strip()
    return val or None

@login_required
def create(request):
    if request.method == 'POST':
        build = SavedBuild.objects.create(
            user=request.user,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            weapon=Weapon.objects.filter(pk=_pk(request.POST, 'weapon')).first(),
            head=Armor.objects.filter(pk=_pk(request.POST, 'head')).first(),
            chest=Armor.objects.filter(pk=_pk(request.POST, 'chest')).first(),
            arms=Armor.objects.filter(pk=_pk(request.POST, 'arms')).first(),
            waist=Armor.objects.filter(pk=_pk(request.POST, 'waist')).first(),
            legs=Armor.objects.filter(pk=_pk(request.POST, 'legs')).first(),
            charm=Charm.objects.filter(pk=_pk(request.POST, 'charm')).first(),
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
        build.weapon = Weapon.objects.filter(pk=_pk(request.POST, 'weapon')).first()
        build.head = Armor.objects.filter(pk=_pk(request.POST, 'head')).first()
        build.chest = Armor.objects.filter(pk=_pk(request.POST, 'chest')).first()
        build.arms = Armor.objects.filter(pk=_pk(request.POST, 'arms')).first()
        build.waist = Armor.objects.filter(pk=_pk(request.POST, 'waist')).first()
        build.legs = Armor.objects.filter(pk=_pk(request.POST, 'legs')).first()
        build.charm = Charm.objects.filter(pk=_pk(request.POST, 'charm')).first()
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


@login_required
def my_builds_json(request):
    builds = SavedBuild.objects.filter(user=request.user).order_by('-created_at').values('pk', 'title')
    return JsonResponse({'builds': list(builds)})


ARMOR_TYPE_TO_SLOT = {'head': 'head', 'chest': 'chest', 'gloves': 'arms', 'waist': 'waist', 'legs': 'legs'}

@login_required
@require_POST
def add_to_build(request):
    build_pk = request.POST.get('build_pk')
    item_type = request.POST.get('item_type')
    item_pk = request.POST.get('item_pk')
    force = request.POST.get('force') == 'true'

    build = get_object_or_404(SavedBuild, pk=build_pk, user=request.user)

    if item_type == 'weapon':
        item = get_object_or_404(Weapon, pk=item_pk)
        existing = build.weapon
        if existing and not force:
            return JsonResponse({'warning': True, 'existing_name': existing.name, 'item_name': item.name})
        build.weapon = item
        build.save()

    elif item_type == 'armor':
        item = get_object_or_404(Armor, pk=item_pk)
        slot = ARMOR_TYPE_TO_SLOT.get(item.armor_type)
        if not slot:
            return JsonResponse({'error': 'Unknown armor type'}, status=400)
        existing = getattr(build, slot)
        if existing and not force:
            return JsonResponse({'warning': True, 'existing_name': existing.name, 'item_name': item.name, 'slot': slot})
        setattr(build, slot, item)
        build.save()

    elif item_type == 'charm':
        item = get_object_or_404(Charm, pk=item_pk)
        existing = build.charm
        if existing and not force:
            return JsonResponse({'warning': True, 'existing_name': existing.name, 'item_name': item.name})
        build.charm = item
        build.save()

    elif item_type == 'decoration':
        item = get_object_or_404(Decoration, pk=item_pk)
        build.decorations.add(item)

    else:
        return JsonResponse({'error': 'Invalid item type'}, status=400)

    return JsonResponse({'success': True})


@login_required
@require_POST
def report_build(request, pk):
    build = get_object_or_404(SavedBuild, pk=pk)
    if build.user == request.user:
        return JsonResponse({'error': 'Cannot report your own build'}, status=400)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Reason is required'}, status=400)
    _, created = BuildReport.objects.get_or_create(
        user=request.user, build=build,
        defaults={'reason': reason}
    )
    if created:
        send_mail(
            subject=f'[Report] Build: {build.title}',
            message=(
                f'Reporter: {request.user.username}\n'
                f'Build: {build.title} (ID: {build.pk})\n'
                f'Author: {build.user.username}\n'
                f'Reason: {reason}\n\n'
                f'Admin link: http://127.0.0.1:8000/admin/builds/savedbuild/{build.pk}/change/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.REPORT_RECIPIENT],
            fail_silently=True,
        )
    return JsonResponse({'reported': True, 'already': not created})


@login_required
@require_POST
def report_build_comment(request, pk):
    comment = get_object_or_404(BuildComment, pk=pk)
    if comment.user == request.user:
        return JsonResponse({'error': 'Cannot report your own comment'}, status=400)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Reason is required'}, status=400)
    _, created = BuildCommentReport.objects.get_or_create(
        user=request.user, comment=comment,
        defaults={'reason': reason}
    )
    if created:
        send_mail(
            subject=f'[Report] Comment on build: {comment.build.title}',
            message=(
                f'Reporter: {request.user.username}\n'
                f'Build: {comment.build.title} (ID: {comment.build.pk})\n'
                f'Comment author: {comment.user.username}\n'
                f'Comment: {comment.text}\n'
                f'Reason: {reason}\n\n'
                f'Admin link: http://127.0.0.1:8000/admin/builds/buildcomment/{comment.pk}/change/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.REPORT_RECIPIENT],
            fail_silently=True,
        )
    return JsonResponse({'reported': True, 'already': not created})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    builds = SavedBuild.objects.filter(user=profile_user, is_public=True).order_by('-created_at')
    return render(request, 'builds/profile.html', {
        'profile_user': profile_user,
        'builds': builds,
    })
