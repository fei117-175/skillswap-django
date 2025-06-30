from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

from BlogPosts.models import BlogPost
from .models import User, UserProfile
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from rest_framework.authtoken.models import Token
import json

# 注册视图
@csrf_exempt  # 临时禁用CSRF便于测试
def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)

    try:
        # 解析JSON数据
        data = json.loads(request.body)

        # 必填字段验证
        required_fields = ['username', 'password', 'confirmPassword']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'message': f'缺少必填字段: {field}'}, status=400)

        # 密码一致性检查
        if data['password'] != data['confirmPassword']:
            return JsonResponse({'message': '两次密码输入不一致'}, status=400)

        # 用户名唯一性检查
        if User.objects.filter(username=data['username']).exists():
            return JsonResponse({'message': '用户名已存在'}, status=409)

        # 创建用户（密码自动加密）
        user = User.objects.create(
            username=data['username'],
            password=make_password(data['password']),
            email=data.get('email'),
            phone=data.get('phone'),
            phone_prefix=data.get('phone_prefix', '+86')
        )

        # 创建用户资料
        skills = data.get('skills', [])
        UserProfile.objects.create(
            user=user,
            skill1=skills[0] if len(skills) > 0 else None,
            skill2=skills[1] if len(skills) > 1 else None,
            skill3=skills[2] if len(skills) > 2 else None
        )

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'username': user.username
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# 登录接口
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import login as auth_login  # 重命名避免冲突
@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data['username']  # 直接获取，避免None
            password = data['password']

            print(f"尝试登录用户: {username}")  # 调试日志

            # 1. 使用authenticate进行认证（推荐方式）
            user = authenticate(request, username=username, password=password)

            if not user:
                print("认证失败：用户名或密码错误")
                return JsonResponse(
                    {'status': 'error', 'message': '用户名或密码错误'},
                    status=401
                )

            # 2. 检查用户状态
            if not user.is_active:
                print("用户未激活")
                return JsonResponse(
                    {'status': 'error', 'message': '用户已被禁用'},
                    status=403
                )
            # 3. 正式登录（设置session和request.user）
            auth_login(request, user)
            # 4. 生成JWT
            refresh = RefreshToken.for_user(user)
            print("登录成功，生成Token")
            avatar_url = user.profile.avatar.url if user.profile.avatar else None
            # print(avatar_url)
            return JsonResponse({
                'message': 'success',
                'username': user.username,
                'avatar': request.build_absolute_uri(avatar_url),
                'sk_id': user.profile.sk_id,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
            })

        except KeyError as e:
            print(f"缺少必要字段: {str(e)}")
            return JsonResponse(
                {'status': 'error', 'message': f'缺少字段: {str(e)}'},
                status=400
            )
        except Exception as e:
            print(f"未知错误: {str(e)}")
            return JsonResponse(
                {'status': 'error', 'message': '服务器错误'},
                status=500
            )


# 验证token接口
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    验证Token有效性
    """
    print('正在验证token....')
    return Response({
        'valid': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username
        }
    })




#登出路由
# 新增注销接口
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()  # 加入黑名单
        return Response({"detail": "登出成功"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)





# 头像处理视图
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.contrib.auth import authenticate, get_user_model
from .models import UserProfile
import os
class AvatarUploadView(APIView):
    """
    头像上传接口
    POST avatar/
    要求: 认证用户 + multipart/form-data
    """
    def post(self, request):
        # 1. 验证用户是否登录
        if not request.user.is_authenticated:
            return Response(
                {'status': 'error', 'message': '未登录'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2. 获取上传的文件
        if 'avatar' not in request.FILES:
            return Response(
                {'status': 'error', 'message': '未提供头像文件'},
                status=status.HTTP_400_BAD_REQUEST
            )
        print("\n=== 请求开始 ===")  # 调试标记
        print("用户认证状态:", request.user.is_authenticated)
        print("上传文件列表:", request.FILES.keys())

        if 'avatar' not in request.FILES:
            return Response(...)

        avatar_file = request.FILES['avatar']
        print("文件名:", avatar_file.name, "大小:", avatar_file.size)
        # 3. 验证文件类型和大小
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_ext = os.path.splitext(avatar_file.name)[1].lower()

        if file_ext not in valid_extensions:
            return Response(
                {'status': 'error', 'message': '仅支持JPG/PNG/GIF格式'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if avatar_file.size > 2 * 1024 * 1024:  # 2MB限制
            return Response(
                {'status': 'error', 'message': '文件大小不能超过2MB'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. 保存头像并更新数据库
        try:
            profile = request.user.profile

            # 删除旧头像
            if profile.avatar and profile.avatar.name != 'avatars/default.jpg':
                profile.avatar.delete()

            # 保存新头像（关键修改：使用FileSystemStorage直接保存）
            fs = default_storage
            filename = f"avatars/user_{request.user.id}/{avatar_file.name}"
            saved_path = fs.save(filename, avatar_file)

            # 更新数据库字段（使用相对路径）
            profile.avatar.name = saved_path  # 如 "avatars/user_1/photo.jpg"
            profile.save()
            print('图片已保存')
            User = get_user_model()
            print(User)
            user = User.objects.get(username=request.user.username)
            print(user)
            avatar_url = user.profile.avatar.url if user.profile.avatar else None
            print(avatar_url)
            # 返回统一格式的路径（关键修改）
            # 返回标准化数据结构
            return Response({
                'status': 'success',
                'avatar_path': request.build_absolute_uri(avatar_url),  # 统一相对路径
                'message': '头像上传成功'
            })

        except Exception as e:
            print(f"头像上传错误: {str(e)}")
            return Response(
                {'status': 'error', 'message': '文件处理失败'},
                status=500
            )





from django.utils.timezone import localtime
#获取个人信息方法（个人主页）
@api_view(['GET'])
@permission_classes([AllowAny])
def userprofile(request, sk_id):
    try:
        # 通过sk_id获取用户资料
        profile = UserProfile.objects.get(sk_id=sk_id)
        user = profile.user

        # 构建响应数据
        data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            },
            'profile': {
                'sk_id': profile.sk_id,
                'age': profile.age,
                'sex': profile.get_sex_display(),
                'bio': profile.bio,
                'avatar': request.build_absolute_uri(profile.avatar.url) if profile.avatar else None,
                'skill1': profile.skill1,
                'skill2': profile.skill2,
                'skill3': profile.skill3,
                'mbti': profile.mbti
            }
        }
        # 如果是查看自己的资料，添加敏感信息
        if request.user.is_authenticated and request.user == user:
            data['user'].update({
                'email': user.email,
                'phone': user.phone,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
            })

        return JsonResponse({
            'status': 'success',
            'data': data
        })

    except UserProfile.DoesNotExist:
        return Response({'error': '用户不存在'}, status=404)
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        return Response({'error': '服务器错误'}, status=500)



from django.db.models import Q
# 通过搜索框获取用户的个人界面所需的博客信息
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_blogs(request, sk_id=None):
    try:
        # 通过sk_id获取用户
        if sk_id:
            profile = UserProfile.objects.get(sk_id=sk_id)
            user = profile.user
        else:
            return Response({'error': '缺少用户标识'}, status=400)

        # 获取博客数据
        # 基础查询：所有公开博客
        query = Q(visibility=0)

        # 如果用户已登录，追加查询条件：或当前用户自己的博客
        if request.user.is_authenticated:
            query |= Q(author=request.user)

        # 最终查询
        blogs = BlogPost.objects.filter(query).order_by('-created_at')

        # 构建响应数据
        blog_list = []
        for blog in blogs:
            blog_data = {
                'id': blog.id,
                'type': 'blog',
                'title': blog.title,
                'content_preview': blog.content[:100] + '...' if len(blog.content) > 100 else blog.content,
                'created_at': blog.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'likes': blog.likes_count,
                'author': {
                    'id': blog.author.id,
                    'username': blog.author.username,
                    'avatar': request.build_absolute_uri(blog.author.profile.avatar.url) if blog.author.profile.avatar else None
                },
                'media': [{
                    'url': request.build_absolute_uri(media.file.url),
                    'type': media.media_type,
                    'thumbnail': request.build_absolute_uri(media.thumbnail.url) if media.thumbnail else None
                } for media in blog.media_files.all()[:3]]  # 只返回前3个媒体文件
            }
            blog_list.append(blog_data)

        return Response({
            'status': 'success',
            'message': '获取博客成功',
            'data': {
                'blog_list': blog_list,
                'total_count': len(blog_list),
                'current_user': request.user.id if request.user.is_authenticated else None
            }
        })

    except UserProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': '用户不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取用户博客失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': '获取博客失败',
            'error': str(e)
        }, status=500)




# 修改个人信息
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
import logging
from datetime import datetime
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_profile(request):
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        user_data = request.data.get('user', {})
        profile_data = request.data.get('profile', {})

        # 更新用户字段
        if 'username' in user_data:
            user.username = user_data['username']
        if 'phone' in user_data:
            user.phone = user_data['phone']
        if 'phone_prefix' in user_data:
            user.phone_prefix = user_data['phone_prefix']

        # 更新资料字段 - 严格匹配模型定义
        if 'sex' in profile_data:
            profile.sex = profile_data['sex']
        if 'age' in profile_data:
            profile.age = profile_data['age']
        if 'birthday' in profile_data:
            try:
                if profile_data['birthday']:  # 确保不是空字符串
                    profile.birthday = datetime.strptime(profile_data['birthday'], '%Y-%m-%d').date()
                else:
                    profile.birthday = None
            except (ValueError, TypeError):
                profile.birthday = None
        if 'mbti' in profile_data:
            profile.mbti = profile_data['mbti']
        if 'skill1' in profile_data:
            profile.skill1 = profile_data['skill1']
        if 'skill2' in profile_data:
            profile.skill2 = profile_data['skill2']
        if 'skill3' in profile_data:
            profile.skill3 = profile_data['skill3']
        if 'bio' in profile_data:
            profile.bio = profile_data['bio']

        user.save()
        profile.save()

        return Response({
            'status': 'success',
            'message': '个人资料更新成功',
            'data': {
                'user': {
                    'username': user.username,
                    'phone': user.phone,
                    'phone_prefix': user.phone_prefix
                },
                'profile': {
                    'sex': profile.sex,
                    'age': profile.age,
                    'birthday': profile.birthday.strftime('%Y-%m-%d') if profile.birthday else None,
                    'mbti': profile.mbti,
                    'skill1': profile.skill1,
                    'skill2': profile.skill2,
                    'skill3': profile.skill3,
                    'bio': profile.bio
                }
            }
        })

    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': '更新用户资料失败',
            'error': str(e)
        }, status=400)



# 修改个人密码
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:
        user = request.user
        data = request.data

        # 验证必需字段
        required_fields = ['old_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return Response({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }, status=400)

        old_password = data['old_password']
        new_password = data['new_password']

        # 验证旧密码
        if not check_password(old_password, user.password):
            return Response({
                'status': 'error',
                'message': '当前密码不正确'
            }, status=400)

        # 验证新密码长度
        if len(new_password) < 8:
            return Response({
                'status': 'error',
                'message': '新密码长度至少需要8个字符'
            }, status=400)

        # 验证新旧密码是否相同
        if old_password == new_password:
            return Response({
                'status': 'error',
                'message': '新密码不能与当前密码相同'
            }, status=400)

        # 更新密码
        user.set_password(new_password)
        user.save()

        # 保持用户登录状态
        update_session_auth_hash(request, user)

        return JsonResponse({
            'status': 'success',
            'message': '密码修改成功'
        })

    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'message': '服务器内部错误',
            'error': str(e)
        }, status=500)

