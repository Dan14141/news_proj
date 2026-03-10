from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User

# Сериализатор для регистрации
class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name',
        )

    # Сравниваем пароль с подтверждением
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match'}
            )
        return attrs

    # Создание пользователя
    def create(self, validated_data):
        # Исключаем поле подтверждения пароля
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

# Сериализатор для входа в аккаунт
class UserLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                # Берём запрос пользователя из контекста
                request=self.context.get('request'),
                username=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    'Username or password is incorrect'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'User is inactive'
                )
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must provide both email and password'
            )

# Сериализатор для профиля пользователя
class UserProfileSerializer(serializers.ModelSerializer):
    # Определяем поле полного имени - только для чтения
    full_name = serializers.ReadOnlyField()
    # Определяем вычисляемые поля количества постов и комментов
    posts_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'avatar', 'bio', 'created_at', 'updated_at',
            'posts_count', 'comments_count'
        )
    read_only_fields = ('id', 'created_at', 'updated_at')

    # Методы счётчиков
    def get_posts_count(self, obj):
        try:
            return obj.posts.count()
        except AttributeError:
            return 0

    def get_comments_count(self, obj):
        try:
            return obj.comments.count()
        except AttributeError:
            return 0

# Сериализатор для изменения данных пользователя
class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'avatar', 'bio'
        )

    # Обновление данных
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

# Сериализатор для смены пароля
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    # Проверка корректности старого пароля
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Password incorrect'
            )
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match'}
            )
        return attrs

    # Переопределение метода save()
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
