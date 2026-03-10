from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, Post

# Сериализатор для категории
class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'posts_count']
        read_only_fields = ['slug', 'created_at']

    # Метод подсчёта опубликованных постов
    def get_posts_count(self, obj):
        return obj.posts.filter(status = 'published').count()

    def create(self, validated_data):
        # Генерация слага
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

# Сериализатор для просмотра постов
class PostListSerializer(serializers.ModelSerializer):
    # Определение полей связанных объектов(автора и категории)
    author = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    comments_count = serializers.ReadOnlyField()
    is_pinned = serializers.ReadOnlyField()
    pinned_info = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug','content','image', 'author',
                  'category','status','views_count', 'comments_count',
                  'created_at', 'updated_at','is_pinned', 'pinned_info',
                  ]
        read_only_fields = ['slug', 'author', 'views_count']

    # Возвращаем информацию о закреплении
    def get_pinned_info(self, obj):
        return obj.get_pinned_info()

    # Метод показа публикации в списке (короткая версия)
    def to_representation(self, instance):
        # Преобразование экземпляра публикациий в словарь
        data = super().to_representation(instance)
        # Обрезаем до 200 символов
        if len(data['content']) > 200:
            data['content'] = data['content'][:200] + '...'
        return data

# Сериализатор для просмотра конкретной публикации
class PostDetailSerializer(serializers.ModelSerializer):

    author_info = serializers.SerializerMethodField()
    category_info = serializers.SerializerMethodField()
    comments_count = serializers.ReadOnlyField()
    is_pinned = serializers.ReadOnlyField()
    pinned_info = serializers.SerializerMethodField()
    can_pin = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug','content','image', 'author',
                  'author_info','category','status','views_count',
                  'comments_count', 'created_at', 'updated_at',
                  'category_info', 'is_pinned', 'pinned_info',
                  'can_pin'
                  ]
    read_only_fields = ['slug', 'author', 'views_count']

    # Получаем расширенную информацию об авторе и категории
    def get_author_info(self, obj):
        # Получаем автора данного поста
        author = obj.author
        return {
            'id': author.id,
            'username': author.username,
            'full_name': author.full_name,
            'avatar': author.avatar.url if author.avatar else None,
        }

    def get_category_info(self, obj):
        if obj.category:
            return {
                'id': obj.category.id,
                'name': obj.category.name,
                'slug': obj.category.slug,
                'description': obj.category.description,
            }
        else:
            return None

    def get_pinned_info(self, obj):
        return obj.get_pinned_info()

    # Проверяем, может ли текущий пользователь закрпить пост
    def get_can_pin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.can_be_pinned_by(request.user)

# Сериализатор для создания/ изменения публикаций
class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image','category', 'status']

    def create(self, validated_data):
        # Назначаем автором текущего пользователя
        validated_data['author'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Если меняется заголовок, то меняем и слаг
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)