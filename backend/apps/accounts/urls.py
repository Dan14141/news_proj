from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# URL-конфигурация для API-эндпоинтов
urlpatterns = [
    # Эндпоинт, API этого эндпоинта, имя для использования в шаблонах
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]