from rest_framework import permissions

# Проверка на авторство
class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Если метод GET, HEAD, OPTIONS, то можно всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Если иной метод, то можно только, если
        # текущий пользователь - автор объекта
        return obj.author == request.user