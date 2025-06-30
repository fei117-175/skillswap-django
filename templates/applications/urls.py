from django.urls import path
from .views import swap_apl,get_all_exchanges,switch,checkselfapl,handle,history,delete,getmatched,getuserplans
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('request/',swap_apl,name='application_swap'),   #发起申请路由
    path('exchange/',get_all_exchanges,name='get_all_exchanges'),  #获取所有申请路由
    path('switch/<int:exchangeId>/',switch,name='application_switch'),  #点击交换
    path('checkselfapl/',checkselfapl,name='checkselfapl'),  #查看用户的申请记录
    path('handle/',handle,name='application_handle'),  #申请状态处理路由
    path('history/',history,name='application_history'),   #历史请求
    path('delete/<int:id>/',delete,name='application_delete'),    #删除请求
    path('getmatched/',getmatched,name='application_getmatched'),   #点击日历获取对应的以匹配的事物。
    path('getuserplans/',getuserplans,name='application_getuserplans'),    #初始化日历方法
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)