from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
import random
import uuid
import os


def user_avatar_path(instance, filename):
    # 头像保存路径: media/avatars/username/filename
    return f'avatars/{instance.username}/{filename}'


class User(AbstractUser):
    # 修复权限字段定义
    groups = models.ManyToManyField(
        Group,  # 第一个参数必须是模型类或模型名称
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        Permission,  # 第一个参数必须是模型类或模型名称
        related_name='custom_user_perm_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='手机号'
    )
    phone_prefix = models.CharField(
        max_length=5,
        default='+86',
        verbose_name='国际区号'
    )
    # 确保自定义字段正确定义
    id = models.AutoField(primary_key=True)  # 明确指定主键

    def save(self, *args, **kwargs):
        # 确保保存的是有效用户
        if not isinstance(self, User):
            raise ValueError("必须保存有效的User实例")
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'login_user'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username



def generate_skid():
    return str(random.randint(10**10, 10**11-1))
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )

    sk_id = models.CharField(
        max_length=11,
        unique=True,
        editable=False,
        default=generate_skid
    )

    age = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)]
    )

    sex = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    )

    birthday = models.DateField(null=True, blank=True)
    mbti = models.CharField(max_length=4, null=True, blank=True)
    skill1 = models.CharField(max_length=50, null=True, blank=True)
    skill2 = models.CharField(max_length=50, null=True, blank=True)
    skill3 = models.CharField(max_length=50, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        default='avatars/default.jpg'
    )

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def username(self):
        """安全访问代理，防止直接属性访问错误"""
        return self.user.username

    def __getattr__(self, name):
        if name == 'username':
            raise AttributeError(
                "直接访问UserProfile.username是禁止的！请使用user.username"
            )
        raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")