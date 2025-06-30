# blogposts/services.py
from .models import BlogPost
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_blogs_status(target_user):
    """
    获取用户博客状态及数据（简化版）

    :param target_user: 已认证的用户对象
    :return: {
        'has_blogs': bool,
        'blogs': queryset or None,
        'count': int
    }
    """
    blogs = BlogPost.objects.filter(author=target_user) \
        .select_related('author') \
        .prefetch_related('media_files') \
        .order_by('-created_at')

    return {
        'has_blogs': blogs.exists(),  # 0/1可由前端转换
        'blogs': blogs if blogs.exists() else None,
        'count': blogs.count()
    }