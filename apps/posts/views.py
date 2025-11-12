from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from.models import Category, Post
from .serializers import (
    CategorySerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer
)
from .permissions import IsAuthorOrReadOnly

# API для создания списка категорий
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # Создание - только для авторизованных
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # Добавление возможности поиска по указанным полям модели и
    # возможности сортировки по указанным полям модели
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    # Список полей для поиска
    search_fields = ['name','description']
    # Список полей для сортировки
    ordering_fields = ['name', 'created_at']
    # Сортировка по умолчанию по имени
    ordering = ['name']

# API для просмотра отдельной категории
class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # Поиск по <slug>
    lookup_field = 'slug'

# API для создания списка постов
class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # Добавление возможности фильтрации
    filter_backends = [DjangoFilterBackend,filters.SearchFilter, filters.OrderingFilter]
    # Список полей для фильтрации
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'views_count', 'title']
    ordering = ['-created_at']

    #  Переопределение метода get_queryset
    def get_queryset(self):

        # Загружаем посты и данные автора, категории для каждого поста
        queryset = Post.objects.select_related('author', 'category')
        # Для неавторизованных пользователей только опубликованные посты
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status = 'published')
        else:
            # Для авторизованных плюсом свои посты любого статуса
            queryset = queryset.filter(Q(status='published') | Q(author=self.request.user))
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer

# API для просмотра конкретного поста
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.select_related('author', 'category')
    serializer_class = PostDetailSerializer
    # Редактирование только для автора
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    # Переопределение метода retrieve
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Добавляем счётчик просмотров
        if request.method == 'GET':
            instance.increment_views_count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# API для промотра своих постов
class MyPostsListView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'views_count', 'title']
    ordering = ['-created_at']

    # Переопределяем: возвращаем только публикации текущего пользователя,
    # с данными об авторе и категории, от новых к старым
    def get_queryset(self):
        return Post.objects.filter(
            author=self.request.user,
        ).select_related('author', 'category').order_by('-created_at')

# API для просмотра постов по категориям (только GET-запросы)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    # Получаем категорию по slug либо возращаем 404
    category = get_object_or_404(Category, slug=category_slug)
    # Получаем опубликованные посты только данной категории
    posts = Post.objects.filter(
        category=category,
        status='published'
    ).select_related('author', 'category').order_by('-created_at')
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({
        'category': CategorySerializer(category).data,
        'posts': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    # Первые 10 публикаций по количеству просмотров
    posts = Post.objects.filter(
        status='published',
    ).select_related('author', 'category').order_by('-views_count')[:10]
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    # Первые 10 публикаций по дате создания
    posts = Post.objects.filter(
        status='published',
    ).select_related('author', 'category').order_by('-created_at')[:10]

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)
