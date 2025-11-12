from rest_framework import serializers
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, PinnedPost, SubscriptionHistory

# Сериализатор для тарифных планов
class SubscriptionPlanSerializer(serializers.ModelSerializer):


    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'price', 'duration_days', 'features',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    #Переопределяем для гарантии корректного вывода
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Убедиться, что feauters - это объект
        if not data.get('features'):
            data['feauters'] = {}
        return data

# Сериализатор для подписки
class SubscriptionSerializer(serializers.ModelSerializer):
    plan_info = SubscriptionPlanSerializer(source='plan', read_only=True)
    user_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_info', 'plan', 'plan_info', 'status',
            'start_date', 'end_date', 'auto_renew', 'is_active',
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]

    # Возвращаем информацию о пользователе
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.full_name,
            'email': obj.user.email,
        }

# Сериализатор для создания подписки
class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ['plan']

    # Валидация тарифного плана
    def validate_plan(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Selected plan is not active.')
        return value

    # Общая валидация
    def validate(self, attrs):
        user = self.context['request'].user

        # Проверяем, есть ли уже активная подписка
        if hasattr(user, 'subscription') and user.subscription.is_active():
            raise serializers.ValidationError({
                'non_field_errors': ['User already has an active subscription.']
            })
        return attrs

    # Метод создания подписки
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending'
        validated_data['start_date'] = timezone.now()
        validated_data['end_date'] = timezone.now()
        return super().create(validated_data)

# Сериализатор закреплённого поста
class PinnedPostSerializer(serializers.ModelSerializer):
    post_info = serializers.SerializerMethodField()

    class Meta:
        model = PinnedPost
        fields = ['id', 'post', 'post_info', 'pinned_at']
        read_only_fields = ['id', 'pinned_at']

    # Возвращаем информацию о посте
    def get_post_info(self, obj):
        return {
            'id': obj.post.id,
            'title': obj.post.title,
            'slug': obj.post.slug,
            'content': obj.post.content,
            'image': obj.post.image,
            'views_count': obj.post.views_count,
            'created_at': obj.post.created_at,
        }

    # Валидация поста для закрепления
    def validate_post(self, value):
        user = self.context['request'].user

        # Проверяем, что пост принадлежит пользователю
        if value.author != user:
            raise serializers.ValidationError('You can ony pinned your posts.')

        # Проверяем, что пост опубликован
        if value.status != 'published':
            raise serializers.ValidationError('Only published posts can be pinned.')
        return value

    # Общая валидация
    def validete(self, attrs):
        user = self.context['request'].user

        # Проверяем, есть ли активная подписка
        if not hasattr(user, 'subscription') or not user.subscription.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['Active subscription required to pin posts.']
            })
        return attrs

    # Метод создания закреплённого поста
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

# Сериализатор для истории подписки
class SubscriptionHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionHistory
        fields = [
            'id', 'action', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Сериализатор для статуса подписки
class UserSubscriptionStatusSerializer(serializers.Serializer):
    has_subscription = serializers.BooleanField()
    is_active = serializers.BooleanField()
    subscription = SubscriptionSerializer(allow_null=True)
    pinned_post = PinnedPostSerializer(allow_null=True)
    can_pin_posts = serializers.BooleanField()

    # Формирование ответа с информацией о подписке
    def to_representation(self, instance):
        user = instance
        has_subscription = hasattr(user, 'subscription')
        subscription = user.subscription if has_subscription else None
        is_active = subscription.is_active if subscription else False
        pinned_post = getattr(user, 'pinned_post', None) if is_active else None

        return {
            'has_subscription': has_subscription,
            'is_active': is_active,
            'subscription': SubscriptionSerializer(subscription).data if subscription else None,
            'pinned_post': PinnedPostSerializer(pinned_post).data if pinned_post else None,
            'can_pin_posts': is_active,
        }

# Сериализатор для закрепления поста
class PinPostSerializer(serializers.Serializer):
    post_id = serializers.IntegerField()

    # Валидация ID поста
    def validate_post_id(self, value):
        from apps.posts.models import Post

        try:
            post = Post.objects.get(id=value, status='published')
        except Post.DoesNotExist:
            raise serializers.ValidationError("Post not found or not published.")

        user = self.context['request'].user
        if post.author != user:
            raise serializers.ValidationError("You can only pin your own posts.")

        return value

    def validate(self, attrs):
        user = self.context['request'].user

        # Проверяем подписку
        if not hasattr(user, 'subscription') or not user.subscription.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['Active subscription required to pin posts.']
            })
        return attrs

#Сериализатор для открепления поста
class UnpinPostSerializer(serializers.Serializer):

    # Валидация открепления поста
    def validate(self, attrs):
        user = self.context['request'].user

        if not hasattr(user, 'pinned_post'):
            raise serializers.ValidationError({
                'non_field_errors': ['No pinned post found.']
            })
        return attrs
