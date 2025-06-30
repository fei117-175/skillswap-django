from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class BlogPost(models.Model):
    VISIBILITY_CHOICES = ((0, '公开'), (1, '私密'))

    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    visibility = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)
    likes_count = models.PositiveIntegerField(default=0,editable=False)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_images = models.PositiveIntegerField(default=9  , editable=False)
    max_videos = models.PositiveIntegerField(default=1, editable=False)

    @property
    def current_image_count(self):
        return self.media_files.filter(media_type='image').count()

    @property
    def current_video_count(self):
        return self.media_files.filter(media_type='video').count()

    def likes(self):
        """动态计算点赞数（优先从缓存字段读取）"""
        return self.likes_count

    def update_likes_count(self):
        """更新点赞数缓存"""
        self.likes_count = self.like_set.count()
        self.save(update_fields=['likes_count'])

    class Meta:
        db_table = 'blog_post'
        indexes = [
            models.Index(fields=['author', 'visibility']),
            models.Index(fields=['created_at']),
        ]


class BlogMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', '图片'),
        ('video', '视频'),
    ]

    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(
        upload_to='blog_media/%Y-%m-%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov', 'avi', 'webm']
            ),
            MaxValueValidator(1024 * 1024 * 500)  # 限制500MB
        ]
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)  # 视频封面
    duration = models.PositiveIntegerField(default=0)  # 视频时长（秒）
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'blog_media'
        ordering = ['order']


class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    depth = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_comment'
        ordering = ['created_at']

#点赞模型
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey('BlogPost', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 确保用户对同一博客只能点赞一次
        db_table = 'blog_like'

# 收藏模型
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 确保用户对同一博客只能收藏一次
        db_table = 'blog_bookmark'
        indexes = [
            models.Index(fields=['user']),
        ]