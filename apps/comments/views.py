from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Comment
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    CommentDetailSerializer
)
from apps.posts.permissions import IsAuthorOrReadOnly
from apps.posts.models import Post

# API для создания постов и просмотра их
class CommentListCreateApiView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_fields = ['post', 'author', 'parent']
    search_fields = ['content']
    ordering_fields = ['created_at','updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return (Comment.objects.filter(is_active=True).select_related
                ('author', 'post', 'parent'))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

# API для просмотра конкретного комментария
class CommentDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.filter(is_active=True).select_related('author', 'post')
    serializer_class = CommentDetailSerializer
    permissions_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CommentUpdateSerializer
        return CommentSerializer

    # Мягкое удаление
    def perform_destroy(self, instance):
        # Помечаем как неактивный
        instance.is_active = False
        instance.save()

# API для просмотра своих комментариев
class MyCommentsAPIView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_fields = ['post', 'parent', 'is_active']
    search_fields = ['content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user).select_related('post', 'parent')

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
# API дял получения комментариев к определенному посту
def post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    # Получаем только основные комментарии
    comments = (Comment.objects.filter(post=post, parent=None,is_active=True)
                .prefetch_related('replies__author').order_by('-created_at'))
    serializer = CommentDetailSerializer(comments, many=True, context={'request': request})
    # Возвращаем данные поста, коментарии, их количество
    return Response({
        'post': {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
        },
        'comments': serializer.data,
        'comments_count': post.comments.filter(is_active=True).count(),
        })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
# API для получения ответов к комментариям
def comment_replies(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id, is_active=True)
    # Получаем ответы для основных комментриев
    replies = Comment.objects.filter(
        parent=parent_comment,
        is_active=True).select_related('author').order_by('created_at')

    serializer = CommentSerializer(parent_comment, context={'request': request})

    # Возвращаем основной комментарий, ответы к нему, их кол-во
    return Response({
        'parent_comment': CommentSerializer(parent_comment, context={'request': request}).data,
        'replies': serializer.data,
        'replies_count': replies.count(),
    })

