from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from login.models import UserProfile
from BlogPosts.models import BlogPost
from applications.models import ExchangeRequest

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return Response([])

    results = []

    # 1. 用户搜索
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(profile__sk_id__icontains=query)
    ).select_related('profile')[:5]

    for user in users:
        results.append({
            'id': user.id,
            'type': 'user',
            'username': user.username,
            'sk_id': user.profile.sk_id if hasattr(user, 'profile') else '',
            'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None
        })

    # 2. 博客搜索
    blogs = BlogPost.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(author__username__icontains=query)
    ).select_related('author')[:5]

    for blog in blogs:
        results.append({
            'id': blog.id,
            'type': 'blog',
            'title': blog.title,
            'content_preview': blog.content[:100],
            'author': {
                'id': blog.author.id,
                'username': blog.author.username
            },
            'created_at': blog.created_at
        })

    # 3. 技能交换搜索
    exchanges = ExchangeRequest.objects.filter(
        Q(course__icontains=query) |
        Q(skill__icontains=query)
    ).select_related('applicant')[:5]

    for exchange in exchanges:
        results.append({
            'id': exchange.id,
            'type': 'exchange',
            'course': exchange.course,
            'skill': exchange.skill,
            'applicant': {
                'id': exchange.applicant.id,
                'username': exchange.applicant.username
            },
            'status': exchange.apl_status
        })

    return Response(results)