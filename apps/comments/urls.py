from django.urls import path
from . import views

urlpatterns = [
    path('', views.CommentListCreateApiView.as_view(), name='comment-list'),
    path('<int:pk>', views.CommentDetailApiView.as_view(), name='comment-detail'),
    path('my-comments', views.MyCommentsAPIView.as_view(), name='my-comments'),
    path('post/<int:post_id>/', views.post_comments, name='post-comments'),
    path('<int:comment_id>/replies/', views.comment_replies, name='comment-replies'),
]