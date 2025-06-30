from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils.dateparse import parse_datetime
from django.db import transaction
from .models import BlogPost, Tag, BlogMedia
import os

User = get_user_model()

# 常量定义
VALID_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
VALID_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi']


def save_blog_post(user, post_data, files):
    """
    保存博客文章到数据库（JWT适配版）
    :param user: 认证用户对象
    :param post_data: 包含博客数据的字典
    :param files: 上传的文件列表
    :return: BlogPost对象
    :raises: ValueError, Exception
    """
    try:
        # 0. 验证用户
        if not isinstance(user, User):
            raise ValueError("必须提供有效的用户实例")

        with transaction.atomic():
            # 1. 创建博客文章
            new_post = BlogPost.objects.create(
                title=post_data.get('title', '无标题'),
                author=user,
                content=post_data.get('content', ''),
                visibility=int(post_data.get('visibility', 0)),
            )

            # 2. 处理标签
            if category := post_data.get('category'):
                tag, _ = Tag.objects.get_or_create(name=category)
                new_post.tags.add(tag)

            # 3. 处理媒体文件
            for index, file in enumerate(files.getlist('images')):
                file_extension = os.path.splitext(file.name)[1].lower()[1:]

                # 验证文件类型
                if file_extension not in VALID_IMAGE_EXTENSIONS + VALID_VIDEO_EXTENSIONS:
                    raise ValueError(f"不支持的文件类型: {file_extension}")

                media_type = 'image' if file_extension in VALID_IMAGE_EXTENSIONS else 'video'

                BlogMedia.objects.create(
                    blog=new_post,
                    file=file,
                    media_type=media_type,
                    order=index
                )

            # 4. 处理自定义时间
            if create_time_str := post_data.get('create_time'):
                create_time = parse_datetime(create_time_str) or \
                              datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
                new_post.created_at = create_time
                new_post.save(update_fields=['created_at'])

            return new_post

    except Exception as e:
        print(f"[ERROR] 保存博客失败: {str(e)}")
        raise  # 向上层传递异常