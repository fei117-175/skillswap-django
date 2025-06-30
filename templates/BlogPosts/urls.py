from django.urls import path
from .views import save ,delete_blog,blogs,getallblogs,addcomment,toggle_like,toggle_bookmark,get_user_bookmarks,get_user_blogs
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('save/', save, name='save'),  # 发布&保存博客
    path('delete/<int:postId>/',delete_blog, name='delete'), #删除博客
    path('blogs/',blogs, name='blogs'),  #获取个人所有博客
    path('getallblogs/',getallblogs, name='getallblogs'),     #index页面获取所有公开博客
    path('addcomment/<int:postId>/',addcomment, name='addcomment'),   #添加评论
    path('toggle_like/<int:postId>/',toggle_like, name='toggle_like'),   #点赞功能
    path('toggle_bookmark/<int:postId>/',toggle_bookmark, name='toggle_bookmark'),    #收藏功能
    path('bookmarks/', get_user_bookmarks, name='user-bookmarks'),   #获取个人收藏列表
    path('posts/<int:postId>/',get_user_blogs, name='user-blogs' ),    #获取点击的博客数据详情
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)