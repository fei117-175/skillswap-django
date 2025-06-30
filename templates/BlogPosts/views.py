from datetime import datetime
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.utils import timezone
import json
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from .blog_post import get_user_blogs_status
from .models import BlogPost, Tag, BlogMedia, Comment, Like
import logging

logger = logging.getLogger(__name__)


# 上传博客
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def save(request):
    try:
        # 1. 基础验证
        if not request.data.get('title'):
            return Response({"error": "标题不能为空"}, status=400)

        # 2. 创建博客主体
        blog = BlogPost.objects.create(
            title=request.data['title'].strip(),
            content=request.data.get('content', ''),
            visibility=int(request.data.get('visibility', 0)),
            author=request.user
        )

        # 2. 处理单个标签（如果请求中有tag字段）
        tag_name = request.data.get('category').strip()  # 获取单个标签
        if tag_name:
            # 获取或创建标签对象
            tag, created = Tag.objects.get_or_create(
                name=tag_name.lower()  # 标签名统一小写处理
            )
            # 添加多对多关系
            blog.tags.add(tag)

        # 3. 处理图片上传
        if 'media_files' in request.FILES:
            for image_file in request.FILES.getlist('media_files'):
                if not image_file.content_type.startswith('image/'):
                    continue

                BlogMedia.objects.create(
                    blog=blog,
                    file=image_file,
                    media_type='image',
                )

        # 4. 获取该作者的所有博客数据
        author_blogs = BlogPost.objects.filter(author=request.user).order_by('-created_at')

        # 5. 构建响应数据
        response_data = []
        for blog in author_blogs:
            blog_list = {
                'id': blog.id,
                'title': blog.title,
                'content': blog.content,
                'bloger': blog.author.username,
                'visibility': blog.visibility,
                'created_at': blog.created_at,
                'updated_at': blog.updated_at,
                'comments': [],
                'images': [
                    request.build_absolute_uri(media.file.url)
                    for media in blog.media_files.all()
                ] if blog.media_files.exists() else [],
            }
            response_data.append(blog_list)

        return Response({
            'status': 'success',
            'data': response_data
        })

    except Exception as e:
        logger.error(f"博客创建失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=400)



# 获取用户个人的博客
@authentication_classes([JWTTokenUserAuthentication])
@permission_classes([IsAuthenticated])
def blogs(request):
    try:
        # 1. 手动验证Token并获取真实用户
        auth = JWTTokenUserAuthentication()
        token_user, _ = auth.authenticate(request)

        # 2. 从数据库获取真实用户对象
        User = get_user_model()
        real_user = User.objects.get(id=token_user.id)
        print(f"真实用户对象: {real_user} (ID: {real_user.id})")  # 调试日志

        # 3. 使用真实用户获取博客数据
        data = get_user_blogs_status(real_user)  # 传入真实用户对象

        # 4. 序列化数据
        response_data = {
            'blog_status': 1 if data['has_blogs'] else 0,
            'count': data['count'],
            'blog_list': [
                {
                    'id': blog.id,
                    'title': blog.title,
                    'visibility': blog.visibility,
                    'bloger': blog.author.username,
                    'likes': blog.likes_count,
                    'comments': [{
                        'id': comment.id,
                        'author': comment.author.username,
                        'content': comment.content,
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'depth': comment.depth,
                    } for comment in blog.comments.filter(parent=None, is_active=True)]
                    if blog.comments.exists() else [],
                    'images': [
                        request.build_absolute_uri(media.file.url)
                        for media in blog.media_files.all()
                    ] if blog.media_files.exists() else [],
                    'created_at': blog.created_at.strftime('%Y-%m-%d')
                }
                for blog in data['blogs']
            ] if data['has_blogs'] else []
        }

        # 5. 返回响应
        return JsonResponse({
            'message': 'success',
            'blogs': response_data
        })

    except User.DoesNotExist:
        return JsonResponse({
            'error': '用户不存在或已被删除'
        }, status=404)

    except Exception as e:
        print(f"获取博客错误: {str(e)}")  # 记录详细错误
        return JsonResponse({
            'error': '服务器内部错误'
        }, status=500)


# 删除博客的视图
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_blog(request, postId):
    try:
        # 1. 获取要删除的博客
        blog = BlogPost.objects.get(id=postId, author=request.user)

        # 2. 执行删除
        blog.delete()

        # 3. 获取删除后该作者的所有博客数据
        author_blogs = BlogPost.objects.filter(author=request.user).order_by('-created_at')

        # 4. 构建响应数据
        response_data = []
        for blog in author_blogs:
            blog_list = {
                'id': blog.id,
                'title': blog.title,
                'content': blog.content,
                'visibility': blog.visibility,
                'created_at': blog.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': blog.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'images': [
                    request.build_absolute_uri(media.file.url)
                    for media in blog.media_files.all()
                ] if blog.media_files.exists() else [],
            }
            response_data.append(blog_list)

        return Response({
            'status': 'success',
            'data': response_data
        })

    except BlogPost.DoesNotExist:
        return Response({
            'status': 'error',
            'message': '博客不存在或无权删除'
        }, status=404)

    except Exception as e:
        logger.error(f"博客删除失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=400)


# 获取所有博客
from django.db.models import Q, Count, Exists, OuterRef, BooleanField, Value, Case, When, F
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import BlogPost, Tag, BlogMedia, Comment, Like


@api_view(['GET'])
@permission_classes([AllowAny])
def getallblogs(request):
    try:
        # 获取当前用户ID（如果已登录）
        user_id = request.user.id if request.user.is_authenticated else None

        # 1. 预取关联数据优化查询
        prefetch_tags = Prefetch('tags', queryset=Tag.objects.all())
        prefetch_media = Prefetch('media_files',
                                  queryset=BlogMedia.objects.order_by('order'))
        prefetch_comments = Prefetch('comments',
                                     queryset=Comment.objects.filter(is_active=True)
                                     .select_related('author__profile')
                                     .order_by('-created_at'))

        # 2. 获取所有公开博客（单次复杂查询）
        public_blogs = BlogPost.objects.filter(
            Q(visibility=0)  # 使用Q对象确保条件表达式正确
        ).select_related('author').prefetch_related(
            prefetch_tags,
            prefetch_media,
            prefetch_comments
        ).order_by('-created_at')

        # 3. 获取用户点赞状态（如果已登录）
        if user_id:
            liked_posts = set(Like.objects.filter(
                user_id=user_id,
                post_id__in=[blog.id for blog in public_blogs]
            ).values_list('post_id', flat=True))
        else:
            liked_posts = set()

        # 4. 获取有博客的标签（优化查询）
        tags_with_counts = Tag.objects.filter(
            blogpost__in=public_blogs
        ).annotate(
            blog_count=Count('blogpost')
        ).order_by('name').distinct()

        # 5. 构建按标签分类的数据结构
        result = []
        for tag in tags_with_counts:
            blogs = public_blogs.filter(tags__id=tag.id).distinct()

            blog_list = []
            for blog in blogs:
                # 处理评论数据
                comments_list = []
                for comment in blog.comments.all():
                    comments_list.append({
                        'id': comment.id,
                        'content': comment.content,
                        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                        'depth': comment.depth,
                        'authorid': comment.author.id,
                        'username': comment.author.username,
                        'avatar': request.build_absolute_uri(comment.author.profile.avatar.url)
                        if hasattr(comment.author, 'profile') and comment.author.profile.avatar
                        else None
                    })

                blog_list.append({
                    'id': blog.id,
                    'title': blog.title,
                    'summary': blog.content[:100] + '...' if len(blog.content) > 100 else blog.content,
                    'author': {
                        'id': blog.author.id,
                        'username': blog.author.username,
                        'avatar': request.build_absolute_uri(blog.author.profile.avatar.url)
                        if hasattr(blog.author, 'profile') and blog.author.profile.avatar
                        else None
                    },
                    'created_at': blog.created_at.strftime('%Y-%m-%d %H:%M'),
                    'likes': blog.likes_count,
                    'is_liked': blog.id in liked_posts if user_id else False,  # 添加点赞状态
                    'comment_count': len(comments_list),
                    'media': [
                        {
                            'id': media.id,
                            'type': media.media_type,
                            'url': request.build_absolute_uri(media.file.url),
                            'thumbnail': request.build_absolute_uri(media.thumbnail.url)
                            if media.thumbnail else None
                        }
                        for media in blog.media_files.all()
                    ],
                    'comments': comments_list
                })

            if blog_list:  # 只包含有博客的标签
                result.append({
                    "tag_id": tag.id,
                    "tag_name": tag.name,
                    "blog_count": len(blog_list),
                    "blogs": blog_list
                })

        return JsonResponse({
            'status': 'success',
            'count': len(result),
            'data': result
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


# 添加博客评论、
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def addcomment(request, postId):
    try:
        # 从JWT token中获取的用户信息
        user = request.user

        # 解析请求数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({
                'status': 'error',
                'message': '无效的JSON数据'
            }, status=status.HTTP_400_BAD_REQUEST)

        content = data.get('content', '').strip()

        # 验证评论内容
        if not content:
            return Response({
                'status': 'error',
                'message': '评论内容不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证博客是否存在
        try:
            blog = BlogPost.objects.get(pk=postId)
        except BlogPost.DoesNotExist:
            return Response({
                'status': 'error',
                'message': '博客不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 创建评论
        comment = Comment.objects.create(
            blog=blog,
            author=user,
            content=content,
            depth=1,  # 默认1级评论
            created_at=timezone.now()
        )

        # 构建返回数据
        response_data = {
            'message': 'success',
            'data': {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'depth': comment.depth,
                'authorid': comment.author.id,
                'username': comment.author.username,
                'avatar': request.build_absolute_uri(comment.author.profile.avatar.url)
                if hasattr(comment.author, 'profile') and comment.author.profile.avatar
                else None
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 点赞功能
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def toggle_like(request, postId):
    try:
        with transaction.atomic():
            # 使用select_for_update锁定记录防止并发问题
            post = BlogPost.objects.select_for_update().get(pk=postId)

            # 获取或创建点赞记录
            like, created = Like.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'user': request.user, 'post': post}
            )

            if not created:
                like.delete()
                post.likes_count = F('likes_count') - 1  # 使用F表达式原子操作
            else:
                post.likes_count = F('likes_count') + 1

            # 保存并立即获取更新后的值
            post.save(update_fields=['likes_count'])
            post.refresh_from_db()

            return JsonResponse({
                'status': 'success',
                'message': '取消点赞成功' if not created else '点赞成功',
                'is_liked': created,  # 改为前端需要的字段名
                'likes_count': post.likes_count,
                'post_id': post.id   # 添加帖子ID便于前端定位
            })

    except BlogPost.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '博客文章不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


# 收藏功能
from django.http import JsonResponse
from .models import Bookmark, BlogPost
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, postId):
    try:
        post = BlogPost.objects.get(id=postId)
        user = request.user

        # 检查是否已收藏
        bookmark, created = Bookmark.objects.get_or_create(
            user=user,
            post=post,
            defaults={'user': user, 'post': post}
        )

        if not created:
            # 如果已存在，则删除(取消收藏)
            bookmark.delete()
            is_bookmarked = False
        else:
            is_bookmarked = True

        return JsonResponse({
            'status': 'success',
            'is_bookmarked': is_bookmarked,
            'post_id': post.id,  # 添加帖子ID
            'bookmark_count': post.bookmark_set.count()
        })

    except BlogPost.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '博客不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 获取用户个人的收藏列表
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_bookmarks(request):
    try:
        # 预取关联的博客和作者信息，优化查询性能
        bookmarks = Bookmark.objects.filter(
            user=request.user
        ).select_related(
            'post__author'
        ).prefetch_related(
            Prefetch('post__media_files', queryset=BlogMedia.objects.filter(media_type='image'))
        ).order_by('-created_at')

        bookmarked_blogs = []
        for bookmark in bookmarks:
            blog = bookmark.post
            # 获取第一张图片作为封面
            cover_image = blog.media_files.filter(media_type='image').first()

            bookmarked_blogs.append({
                'id': blog.id,
                'title': blog.title,
                'description': blog.content[:100] + '...' if len(blog.content) > 100 else blog.content,
                'author': blog.author.username,
                'date': blog.created_at.strftime('%Y-%m-%d'),
                'category': blog.tags.first().name if blog.tags.exists() else '未分类',
                'image': request.build_absolute_uri(cover_image.file.url) if cover_image else None,
                'url': f'/blog/{blog.id}/',
                'isFavorite': True
            })

        return JsonResponse({
            'status': 'success',
            'data': bookmarked_blogs,
            'count': len(bookmarked_blogs)
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 获取单个博客方法
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_blogs(request, postId):
    print('需要获取的博客数据id是', postId)
    try:
        # 获取当前用户（用于判断是否点赞/收藏）
        current_user = request.user if request.user.is_authenticated else None
        # 查询博客及关联数据（使用prefetch_related优化查询）
        blog = BlogPost.objects.filter(pk=postId).select_related(
            'author'
        ).prefetch_related(
            Prefetch('media_files', queryset=BlogMedia.objects.order_by('order')),
            Prefetch('comments', queryset=Comment.objects.select_related('author').order_by('-created_at')),
            'tags'
        ).annotate(
            total_likes=Count('like'),
            comment_count=Count('comments')
        ).first()
        if not blog:
            return JsonResponse({
                'status': 'error',
                'message': '博客不存在'
            })
        # 构建响应数据
        response_data = {
            #获取blog表中的基础信息
            'id': blog.id,
            'title': blog.title,
            'content': blog.content,
            'created_at': blog.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': blog.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'visibility': blog.get_visibility_display(),
            'likes_count': blog.likes_count,
            'comment_count': blog.comment_count,
            'is_liked': Like.objects.filter(user=current_user, post=blog).exists() if current_user else False,
            'is_bookmarked': Bookmark.objects.filter(user=current_user, post=blog).exists() if current_user else False,
            #获取作者信息
            'blogauthorid': blog.author.id,
            'username': blog.author.username,
            'avatar': request.build_absolute_uri(blog.author.profile.avatar.url) if blog.author.profile.avatar else None,
            #获取照片
            'media': [
                {
                    'id': media.id,
                    'type': media.media_type,
                    'url': request.build_absolute_uri(media.file.url),
                    'thumbnail': media.thumbnail.url if media.thumbnail else None,
                    'duration': media.duration if media.media_type == 'video' else None
                } for media in blog.media_files.all()
            ],
            #获取评论内容
            'comments': [
                {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'authorid': comment.author.id,
                    'username': comment.author.username,
                    'avatar': request.build_absolute_uri(comment.author.profile.avatar.url) if comment.author.profile.avatar else None
                } for comment in blog.comments.all()
            ],
            #获取标签
            'tags': [tag.name for tag in blog.tags.all()]
        }
        return JsonResponse({
            'status': 'success',
            'data': response_data
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        })
