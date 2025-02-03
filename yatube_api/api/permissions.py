from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет редактировать посты только их авторам.
    Остальные пользователи могут только просматривать посты.
    """

    def has_object_permission(self, request, view, obj, *args, **kwargs):
        # Позволяем доступ к объекту, если пользователь автор поста
        return obj.author == request.user or request.method in permissions.SAFE_METHODS


class IsFollowing(permissions.BasePermission):
    """
    Разрешение, которое позволяет пользователю подписываться на других пользователей.
    """

    def has_permission(self, request, view):
        # Разрешаем доступ, если пользователь аутентифицирован
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj, *args, **kwargs):
        # Проверяем, что пользователь не пытается подписаться на себя
        return obj != request.user
    