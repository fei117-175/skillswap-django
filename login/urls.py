from django.urls import path
from .views import register_view,login,AvatarUploadView,verify_token,logout,userprofile,change_profile,change_password,get_user_blogs
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
    path('login/', login, name='login'),  # 登录
    path('register/', register_view, name='register'),  # 注册
    path('avatar/',AvatarUploadView.as_view(), name='avatar'),  #头像更新
    path('api/verify/', verify_token, name='token_verify'),   #token验证
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), #token刷新
    path('logout/', logout, name='logout'),  #登出
    path('user/profile/<str:sk_id>/', userprofile, name='userprofile'),   #获取个人信息
    path('user/blogs/<str:sk_id>/',get_user_blogs,name='get_user_blogs'),  #通过搜索框获取他人博客信息
    path('user/change_profile/',change_profile, name='change_profile'),    #修改个人信息。
    path('user/change_password/',change_password, name='change_password'),   #修改密码
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)