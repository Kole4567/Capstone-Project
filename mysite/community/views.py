from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from .models import CommunityPost, CommunityComment, CommunityPostReport, CommunityCommentReport


def feed(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'recent')

    posts = CommunityPost.objects.select_related('user').prefetch_related(
        'upvotes', 'community_comments'
    ).annotate(
        upvotes_count=Count('upvotes', distinct=True),
        comments_count=Count('community_comments', distinct=True),
    )

    if q:
        posts = posts.filter(title__icontains=q)

    if sort == 'upvotes':
        posts = posts.order_by('-upvotes_count', '-created_at')
    elif sort == 'comments':
        posts = posts.order_by('-comments_count', '-created_at')
    else:
        posts = posts.order_by('-created_at')

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    cur = page_obj.number
    total = page_obj.paginator.num_pages
    page_range = list(range(max(1, cur - 1), min(total, cur + 1) + 1))

    filter_qs = ''
    if q:
        filter_qs += f'q={q}&'
    if sort and sort != 'recent':
        filter_qs += f'sort={sort}&'

    upvoted_ids = set()
    if request.user.is_authenticated:
        upvoted_ids = set(
            CommunityPost.objects.filter(upvotes=request.user).values_list('pk', flat=True)
        )

    return render(request, 'community/feed.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'page_range': page_range,
        'filter_qs': filter_qs,
        'upvoted_ids': upvoted_ids,
        'q': q,
        'sort': sort,
    })


@login_required
def create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if title and content:
            post = CommunityPost.objects.create(
                user=request.user,
                title=title,
                content=content,
            )
            return redirect('community_detail', pk=post.pk)

    return render(request, 'community/create.html')


def detail(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    upvoted = False
    if request.user.is_authenticated:
        upvoted = post.upvotes.filter(pk=request.user.pk).exists()

    comments = post.community_comments.select_related('user').order_by('created_at')

    return render(request, 'community/detail.html', {
        'post': post,
        'upvoted': upvoted,
        'comments': comments,
    })


@login_required
def my_posts(request):
    posts = CommunityPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'community/my_posts.html', {'posts': posts})


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(CommunityPost, pk=request.POST.get('pk') or pk, user=request.user)
    post.delete()
    return redirect('my_posts_community')


@login_required
@require_POST
def upvote(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    if post.upvotes.filter(pk=request.user.pk).exists():
        post.upvotes.remove(request.user)
        upvoted = False
    else:
        post.upvotes.add(request.user)
        upvoted = True
    return JsonResponse({'upvoted': upvoted, 'count': post.upvote_count()})


@login_required
@require_POST
def report_post(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    if post.user == request.user:
        return JsonResponse({'error': 'Cannot report your own post'}, status=400)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Reason is required'}, status=400)
    _, created = CommunityPostReport.objects.get_or_create(
        user=request.user, post=post,
        defaults={'reason': reason}
    )
    if created:
        send_mail(
            subject=f'[Report] Community Post: {post.title}',
            message=(
                f'Reporter: {request.user.username}\n'
                f'Post: {post.title} (ID: {post.pk})\n'
                f'Author: {post.user.username}\n'
                f'Reason: {reason}\n\n'
                f'Admin link: http://127.0.0.1:8000/admin/community/communitypost/{post.pk}/change/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.REPORT_RECIPIENT],
            fail_silently=True,
        )
    return JsonResponse({'reported': True, 'already': not created})


@login_required
@require_POST
def report_comment(request, pk):
    comment = get_object_or_404(CommunityComment, pk=pk)
    if comment.user == request.user:
        return JsonResponse({'error': 'Cannot report your own comment'}, status=400)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Reason is required'}, status=400)
    _, created = CommunityCommentReport.objects.get_or_create(
        user=request.user, comment=comment,
        defaults={'reason': reason}
    )
    if created:
        send_mail(
            subject=f'[Report] Comment on: {comment.post.title}',
            message=(
                f'Reporter: {request.user.username}\n'
                f'Post: {comment.post.title} (ID: {comment.post.pk})\n'
                f'Comment author: {comment.user.username}\n'
                f'Comment: {comment.body}\n'
                f'Reason: {reason}\n\n'
                f'Admin link: http://127.0.0.1:8000/admin/community/communitycomment/{comment.pk}/change/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.REPORT_RECIPIENT],
            fail_silently=True,
        )
    return JsonResponse({'reported': True, 'already': not created})


@login_required
@require_POST
def comment(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    body = request.POST.get('body', '').strip()
    if body:
        c = CommunityComment.objects.create(user=request.user, post=post, body=body)
        return JsonResponse({
            'username': c.user.username,
            'body': c.body,
            'created_at': c.created_at.strftime('%b %d, %Y'),
        })
    return JsonResponse({'error': 'Empty comment'}, status=400)
