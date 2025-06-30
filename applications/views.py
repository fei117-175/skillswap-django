from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import ExchangeRequest
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
import json


# Create your views here.
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def swap_apl(request):
    try:
        # 直接解析原始数据（不验证）
        user = request.user
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST.dict()

        # 直接创建记录（不做任何处理）
        record = ExchangeRequest.objects.create(
            course=data.get('course', ''),
            course_category=data.get('course_category', ''),
            course_subcategory=data.get('course_subcategory', ''),
            skill=data.get('skill', ''),
            skill_category=data.get('skill_category', ''),
            skill_subcategory=data.get('skill_subcategory', ''),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time', ''),
            description=data.get('description', ''),
            apl_status='pending',
            applicant=user,
        )

        # 返回成功（只返回ID）
        return JsonResponse({
            'message': 'success',
            'applicant': user.username,
        }, status=201)

    except Exception as e:
        # 仅捕获最基础错误
        return JsonResponse({
            'error': '存储失败',
            'detail': str(e)
        }, status=500)


# 获取所有申请信息
@require_GET
def get_all_exchanges(request):
    try:
        # 获取所有交换申请，按创建时间倒序排列
        exchanges = ExchangeRequest.objects.all().order_by('-created_at')
        # 转换数据格式，使其更简洁易用
        result = []
        for exchange in exchanges:
            result.append({
                'id': exchange.id,
                'course': exchange.course,
                'skill': exchange.skill,
                'course_category': exchange.course_category,
                'skill_category': exchange.skill_category,
                'skill_subcategory': exchange.skill_subcategory,
                'course_subcategory': exchange.course_subcategory,
                'start_time': exchange.start_time,
                'end_time': exchange.end_time,
                'description': exchange.description,
                'apl_status': exchange.apl_status,
                'applicant_username': exchange.applicant.username if exchange.applicant else None,
                'applicant_avatar': request.build_absolute_uri(
                    exchange.applicant.profile.avatar.url) if exchange.applicant else None,
            })

        return JsonResponse({
            'status': 'success',
            'data': result,
            'count': len(result)
        }, status=200)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 申请交换
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def switch(request, exchangeId):
    try:
        # 1. 获取交换请求对象（如果不存在则返回404）
        exchange_request = ExchangeRequest.objects.get(id=exchangeId)

        # 2. 检查当前用户是否有权限操作（必须是申请人或被申请人）
        if exchange_request.applicant.username != request.user.username:
            # 3. 执行交换逻辑（根据你的业务需求补充）
            exchange_request.accepted_by = request.user  # 将同意者名字添加到对应的事务当中
            exchange_request.apl_status = 'waiting'  # 改为待回应
            exchange_request.save()
            # 4. 返回成功响应
            return JsonResponse(
                {'message': '交换成功'},
                status=200
            )
        return JsonResponse({
            'error': '申请人不能同意自己的交换请求'
        }, status=400)
    except ExchangeRequest.DoesNotExist:
        return JsonResponse(
            {'error': '交换请求不存在'},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'服务器错误: {str(e)}'},
            status=500
        )


# 返回所有与用户有关的申请（已发出pending&&以匹配match&&待回应waiting）
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def checkselfapl(request):
    try:
        user = request.user
        requests = ExchangeRequest.objects.filter(
            Q(applicant=user) | Q(accepted_by=user)
        ).select_related('applicant', 'accepted_by')

        data = []
        for req in requests:
            data.append({
                'id': req.id,
                'course': req.course,
                'skill': req.skill,
                'course_category': req.course_category,
                'skill_category': req.skill_category,
                'skill_subcategory': req.skill_subcategory,
                'course_subcategory': req.course_subcategory,
                'start_time': req.start_time.isoformat() if req.start_time else None,
                'end_time': req.end_time.isoformat() if req.end_time else None,
                'description': req.description,
                'apl_status': req.apl_status,
                'applicant_username': req.applicant.username if req.applicant else None,
                'applicant_avatar': request.build_absolute_uri(
                    req.applicant.profile.avatar.url
                ) if req.applicant and hasattr(req.applicant, 'profile') and req.applicant.profile.avatar else None,
                'accepted_by_username': req.accepted_by.username if req.accepted_by else None,
                'accepted_by_avatar': request.build_absolute_uri(
                    req.accepted_by.profile.avatar.url
                ) if req.accepted_by and hasattr(req.accepted_by,
                                                 'profile') and req.accepted_by.profile.avatar else None,
            })
        return JsonResponse({
            'message': 'success',
            'data': data
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from .models import ExchangeRequest


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def handle(request):
    user = request.user
    try:
        # 解析请求数据
        try:
            data = json.loads(request.body)
            # print('从前端传的信息：', data)
        except json.JSONDecodeError:
            return JsonResponse({
                'code': 400,
                'message': '无效的JSON格式',
                'data': None
            }, status=400)

        application_id = data.get('application_id')
        action = data.get('action')
        print(application_id, action)
        # 验证必要参数
        if not application_id or not action:
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数(application_id或action)',
                'data': None
            }, status=400)

        # 获取交换请求
        try:
            exchange_request = ExchangeRequest.objects.get(id=application_id)
        except ExchangeRequest.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '未找到该交换请求',
                'data': None
            }, status=404)
        # 权限验证和业务逻辑处理
        if action == 1:  # 接受
            # 只有发布方可以接受请求
            if exchange_request.applicant != user:
                return JsonResponse({
                    'code': 403,
                    'message': '只有发布方可以接受请求',
                    'data': None
                }, status=403)

            exchange_request.apl_status = 'matched'
            exchange_request.save()

        elif action == 2:  # 拒绝
            # 只有发布方可以拒绝请求
            if exchange_request.applicant != user:
                return JsonResponse({
                    'code': 403,
                    'message': '只有发布方可以拒绝请求',
                    'data': None
                }, status=403)

            exchange_request.apl_status = 'rejected'
            exchange_request.save()


        elif action == 3:  # 取消操作
            # 检查权限：只有发起方或接受方可以取消
            if exchange_request.applicant == user or exchange_request.accepted_by == user:
                exchange_request.apl_status = 'canceled'  # 仅更新状态字段
                exchange_request.save()  # 保存到数据库
                return JsonResponse({
                    'status': 'success',
                    'message': '交换请求已取消'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '无权取消此请求'
                }, status=403)
        else:
            return JsonResponse({
                'code': 400,
                'message': '无效的操作类型',
                'data': None
            }, status=400)

        return JsonResponse({
            'code': 200,
            'message': '操作成功',
            'data': {
                'application_id': application_id,
                'new_status': exchange_request.apl_status
            }
        })

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def history(request):
    try:
        user = request.user
        # 基础查询：用户是申请人或接受方，且状态为历史状态
        queryset = ExchangeRequest.objects.filter(
            Q(applicant=user) | Q(accepted_by=user),
            apl_status__in=['expired', 'completed', 'canceled']
        ).order_by('-created_at')

        # print(queryset)
        # 构造响应数据
        data = []
        for req in queryset:
            data.append({
                'id': req.id,
                'course': req.course,
                'skill': req.skill,
                'course_category': req.course_category,
                'skill_category': req.skill_category,
                'skill_subcategory': req.skill_subcategory,
                'course_subcategory': req.course_subcategory,
                'start_time': req.start_time.isoformat() if req.start_time else None,
                'end_time': req.end_time.isoformat() if req.end_time else None,
                'description': req.description,
                'apl_status': req.apl_status,
                'applicant_username': req.applicant.username if req.applicant else None,
                'applicant_avatar': request.build_absolute_uri(
                    req.applicant.profile.avatar.url
                ) if req.applicant and hasattr(req.applicant, 'profile') and req.applicant.profile.avatar else None,
                'accepted_by_username': req.accepted_by.username if req.accepted_by else None,
                'accepted_by_avatar': request.build_absolute_uri(
                    req.accepted_by.profile.avatar.url
                ) if req.accepted_by and hasattr(req.accepted_by,
                                                 'profile') and req.accepted_by.profile.avatar else None,
            })
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'data': data
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete(request, id):
    try:
        user = request.user
        # 验证ID是否为有效整数
        print('要删除的记录', id)
        # 查找申请记录
        try:
            exchange = ExchangeRequest.objects.get(id=id)
        except ExchangeRequest.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到该交换申请'
            }, status=404)

        # 权限验证：只有申请人或接受方可以删除
        if exchange.applicant != user and exchange.accepted_by != user:
            return JsonResponse({
                'status': 'error',
                'message': '无权删除此申请'
            }, status=403)

        # 检查申请状态是否允许删除（可选）
        if exchange.apl_status == 'completed':
            return JsonResponse({
                'status': 'error',
                'message': '已完成申请不可删除'
            }, status=400)

        # 执行删除
        exchange.delete()

        return JsonResponse({
            'status': 'success',
            'message': '申请已删除',
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getmatched(request):
    user = request.user
    date_str = request.GET.get('date')
    print('请求的用户为:', request.user)
    if not date_str:
        return JsonResponse({'status': 'error', 'message': '缺少date参数'}, status=400)

    try:
        # 1. 解析前端传入的日期
        input_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        input_datetime = timezone.make_aware(datetime.combine(input_date, datetime.min.time()))

        # 2. 查询用户相关的所有matched申请
        queryset = ExchangeRequest.objects.filter(
            (Q(applicant=user) | Q(accepted_by=user)),
            apl_status__in=['matched', 'completed']
        ).order_by('-created_at')
        print('查询到的数据', queryset)
        # 3. 筛选并计算持续天数
        result = []
        for req in queryset:
            # 计算持续天数
            day_counts = (req.end_time.date() - req.start_time.date()).days + 1
            # 检查输入日期是否在申请的时间范围内
            if req.start_time.date() <= input_date <= req.end_time.date():
                result.append({
                    'id': req.id,
                    'course': req.course,
                    'skill': req.skill,
                    'course_category': req.course_category,
                    'skill_category': req.skill_category,
                    'skill_subcategory': req.skill_subcategory,
                    'course_subcategory': req.course_subcategory,
                    'start_time': req.start_time.isoformat() if req.start_time else None,
                    'end_time': req.end_time.isoformat() if req.end_time else None,
                    'day_counts': day_counts,
                    'description': req.description,
                    'apl_status': req.apl_status,
                    'applicant_username': req.applicant.username if req.applicant else None,
                    'applicant_avatar': request.build_absolute_uri(
                        req.applicant.profile.avatar.url
                    ) if req.applicant and hasattr(req.applicant, 'profile') and req.applicant.profile.avatar else None,
                    'accepted_by_username': req.accepted_by.username if req.accepted_by else None,
                    'accepted_by_avatar': request.build_absolute_uri(
                        req.accepted_by.profile.avatar.url
                    ) if req.accepted_by and hasattr(req.accepted_by,
                                                     'profile') and req.accepted_by.profile.avatar else None,
                })
        return JsonResponse({'message': 'success', 'data': result})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '日期格式无效'}, status=400)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getuserplans(request):
    user = request.user
    # print('请求的用户为:', request.user)
    try:
        # 1. 查询用户相关的所有matched或者是competed申请
        queryset = ExchangeRequest.objects.filter(
            (Q(applicant=user) | Q(accepted_by=user)),
            apl_status__in=['matched', 'completed']
        ).order_by('-created_at')
        # print('查询到的所有数据', queryset)
        # 3. 筛选并计算持续天数
        userallapl = []
        for req in queryset:
            # 计算持续天数
            day_counts = (req.end_time.date() - req.start_time.date()).days + 1
            userallapl.append({
                'id': req.id,
                'apl_status': req.apl_status,
                'day_counts': day_counts,
                'applicant_username': req.applicant.username if req.applicant else None,
                'accepted_by_username': req.accepted_by.username if req.accepted_by else None,
                'start_time': req.start_time.isoformat() if req.start_time else None,
                'end_time': req.end_time.isoformat() if req.end_time else None,
            })
        # print(userallapl)
        return JsonResponse({'message': 'success', 'data': userallapl})
    except ValueError:
        return JsonResponse({'status': 'error', 'message': '日期格式无效'}, status=400)
