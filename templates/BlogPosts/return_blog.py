from rest_framework import serializers
from .models import BlogPost, BlogMedia, Tag
from django.contrib.auth import get_user_model

User = get_user_model()


class BlogMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogMedia
        fields = ['id', 'file', 'media_type', 'thumbnail', 'duration', 'order']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = fields


class BlogPostSerializer(serializers.ModelSerializer):
    media_files = BlogMediaSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # 改为接受ID
    content = serializers.CharField(allow_blank=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'author', 'content',
            'visibility', 'likes', 'tags',
            'media_files', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'likes', 'author'
        ]


class BlogListSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    author_username = serializers.CharField(source='author.username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'author_username',
            'visibility', 'likes', 'created_at',
            'cover_image', 'tags'
        ]

    def get_cover_image(self, obj):
        first_media = obj.media_files.filter(media_type='image').first()
        if first_media:
            return first_media.file.url
        return None