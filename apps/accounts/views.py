from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)


# API для регистрации пользователя
class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    # Доступно всем
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Вызов create() из сериализатора
        user = serializer.save()
        # Генерация JWT-токена
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Successful registration',
        }, status=status.HTTP_201_CREATED)

# API для входа в аккаунт
class UserLoginAPIView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Достаём пользователя из валидированных данных и логиним
        user = serializer.validated_data['user']
        login(request, user)

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Successful user login',
        }, status=status.HTTP_200_OK)

# API для просмотра/обновления профиля
class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    # Доступно только для авторизованных
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    # для PUT, PATCH - обновление, для GET - просмотр профиля
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserProfileSerializer

# API для изменения пароля
class ChangePasswordAPIView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password successfully changed',

        }, status=status.HTTP_200_OK)

# Функциональный API для выхода из профиля
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            # Валидация токена
            # и помещение его в черный список
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            'message': 'Successful logout',
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'error': 'Invalid token',
        }, status=status.HTTP_400_BAD_REQUEST)
