from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from apps.comments.models import Comment

# Модель категории публикации
class Category(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    # Переопределение метода save() для модели
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# Менеджер для модели Post с дополнительными методами
class PostManager(models.Manager):

    def published(self):
        return self.filter(status='published')

    def pinned_posts(self):
        # Возвращаем закрепленные посты в порядке закрепления
        return self.filter(
            pin_info__isnull=False,
            pin_info__user__subscription__status='active',
            pin_info__user__subscription__end_date__gt=models.functions.Now(),
            status='published'
        ).select_related(
            'pin_info', 'pin_info__user', 'pin_info__user__subscription'
        ).order_by('pin_info__pinned_at')

    def regular_posts(self):
        # Возвращаем обычные (незакрепленные) посты
        return self.filter(pin_info__isnull=True, status='published')

    def with_subscription_info(self):
        # Добавляем информацию о подписке автора
        return self.select_related(
            'author', 'author__subscription', 'category'
        ).prefetch_related('pin_info')

# Модель публикации
class Post(models.Model):
    # Варианты статуса публикации
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    # Связь с категорией
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL, # не трогаем посты
        blank=True,
        null=True,
        related_name='posts',
    )
    # Связь с пользователем
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # обнуляем посты
        related_name='posts',
    )
    objects = PostManager()

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        # Определение индексов для бд
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    # Генерация ссылки до конкретной публикации
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'slug': self.slug})

    # Подсчёт количества комментариев к публикации
    @property
    def comments_count(self):
        return Comment.objects.filter(post=self).count()

    # Проверка, закреплен ли пост
    @property
    def is_pinned(self):
        return hasattr(self, 'pin_info') and self.pin_info is not None

    # Проверка, можно ли закрепить этот пост
    @property
    def can_be_pinned_by_user(self):

        # Это свойство не должно принимать параметры
        # Логика проверки должна быть вынесена в отдельный метод

        # Пост должен быть опубликован
        if self.status != 'published':
            return False
        return True

    # Проверка, может ли пользователь закрепить этот пост
    def can_be_pinned_by(self, user):
        if not user or not user.is_authenticated:
            return False

        # Пост должен принадлежать пользователю
        if self.author != user:
            return False

        # Пост должен быть опубликован
        if self.status != 'published':
            return False

        # У пользователя должна быть активная подписка
        if not hasattr(user, 'subscription') or not user.subscription.is_active:
            return False
        return True

    # Увеличение количества просмотров публикации
    def increment_views_count(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    # Возвращаем информацию о закреплении поста
    def get_pinned_info(self):
        if self.is_pinned:
            return {
                'is_pinned': True,
                'pinned_at': self.pin_info.pinned_at,
                'pinned_by': {
                    'id': self.pin_info.user.id,
                    'username': self.pin_info.user.username,
                    'has_active_subscription': self.pin_info.user.subscription.is_active
                }
            }
        return {'is_pinned': False}