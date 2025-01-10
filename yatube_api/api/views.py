from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .pagination import PostPagination
from posts.models import Post, Follow, Comment, Group
from . import serializers
from django.contrib.auth.models import User


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()  # Получаем все посты
    serializer_class = serializers.PostSerializer  # Указываем сериализатор
    pagination_class = PostPagination  # Указываем класс пагинации

    def get_permissions(self):
        # Устанавливаем права доступа в зависимости от действия
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]  # Доступ для всех
        return [permissions.IsAuthenticated()]  # Доступ только для аутентифицированных пользователей

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # Получаем queryset
        page = self.paginate_queryset(queryset)  # Пагинация
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # Сериализация данных
            return self.get_paginated_response(serializer.data)  # Возвращаем пагинированный ответ

        serializer = self.get_serializer(queryset, many=True)  # Сериализация всех данных
        return Response(serializer.data)  # Возвращаем ответ

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)  # Получаем данные из запроса
        serializer.is_valid(raise_exception=True)  # Проверяем валидность данных
        serializer.save(author=request.user)  # Сохраняем пост с автором
        return Response(serializer.data, status=status.HTTP_201_CREATED)  # Возвращаем созданный пост

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()  # Получаем конкретный пост
        serializer = self.get_serializer(post)  # Сериализация поста
        return Response(serializer.data)  # Возвращаем данные поста

    def partial_update(self, request, pk=None):
        post = self.get_object()  # Получаем пост для частичного обновления
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN  # Запрещаем изменение чужого поста
            )
        serializer = self.get_serializer(post, data=request.data, partial=True)  # Сериализация с частичными данными
        serializer.is_valid(raise_exception=True)  # Проверяем валидность
        serializer.save()  # Сохраняем изменения
        return Response(serializer.data)  # Возвращаем обновленные данные

    def update(self, request, pk=None):
        post = self.get_object()  # Получаем пост для полного обновления
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN  # Запрещаем изменение чужого поста
            )
        serializer = self.get_serializer(post, data=request.data)  # Сериализация с новыми данными
        serializer.is_valid(raise_exception=True)  # Проверяем валидность
        serializer.save()  # Сохраняем изменения
        return Response(serializer.data)  # Возвращаем обновленные данные

    def destroy(self, request, pk=None):
        post = self.get_object()  # Получаем пост для удаления
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете удалить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN  # Запрещаем удаление чужого поста
            )
        post.delete()  # Удаляем пост
        return Response(status=status.HTTP_204_NO_CONTENT)  # Возвращаем статус 204 - нет содержимого


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()  # Получаем все группы
    serializer_class = serializers.GroupSerializer  # Указываем сериализатор
    permission_classes = [permissions.AllowAny]  # Разрешаем доступ всем пользователям

    def list(self, request, *args, **kwargs):
        self.pagination_class = None  # Отключаем пагинацию
        return super().list(request, *args, **kwargs)  # Вызываем родительский метод

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)  # Вызываем родительский метод


class FollowViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.FollowSerializer  # Указываем сериализатор
    permission_classes = [permissions.IsAuthenticated]  # Доступ только для аутентифицированных пользователей

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)  # Фильтруем подписки по текущему пользователю

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', None)  # Получаем параметр поиска
        queryset = self.get_queryset()  # Получаем базовый queryset
        if search:
            # Фильтруем подписки по имени пользователя
            queryset = queryset.filter(following__username__icontains=search)
        serializer = self.get_serializer(queryset, many=True)  # Сериализуем данные
        return Response(serializer.data)  # Возвращаем ответ с данными

    def create(self, request, *args, **kwargs):
        following_username = request.data.get('following')  # Получаем имя пользователя, на которого подписываемся
        if not following_username:
            return Response(
                {"following": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST  # Возвращаем ошибку, если поле пустое
            )

        if following_username == request.user.username:
            return Response(
                {"error": "Вы не можете подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST  # Возвращаем ошибку, если пользователь пытается подписаться на себя
            )

        try:
            following_user = User.objects.get(username=following_username)  # Ищем пользователя по имени
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден."},
                status=status.HTTP_404_NOT_FOUND  # Возвращаем ошибку, если пользователь не найден
            )

        if Follow.objects.filter(user=request.user, following=following_user).exists():
            return Response(
                {"error": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST  # Возвращаем ошибку, если подписка уже существует
            )

        # Создаем новую подписку
        Follow.objects.create(user=request.user, following=following_user)

        return Response(
            {
                "user": request.user.username,
                "following": following_user.username
            },
            status=status.HTTP_201_CREATED  # Возвращаем успешный ответ
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer  # Указываем сериализатор для комментариев
    permission_classes = [permissions.IsAuthenticated]  # Доступ только для аутентифицированных пользователей

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]  # Разрешаем доступ всем
        else:
            permission_classes = [permissions.IsAuthenticated]  # Остальные действия требуют аутентификации
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        post_id = self.kwargs['post_id']  # Получаем ID публикации из URL
        return Comment.objects.filter(post_id=post_id)  # Фильтруем комментарии по ID публикации

    def list(self, request, post_id=None):
        try:
            Post.objects.get(id=post_id)  # Проверяем, существует ли публикация
        except Post.DoesNotExist:
            raise NotFound("Публикация не найдена.")  # Возвращаем ошибку, если публикация не найдена

        comments = self.get_queryset()  # Получаем комментарии
        serializer = self.get_serializer(comments, many=True)  # Сериализуем данные
        return Response(serializer.data)  # Возвращаем ответ с данными

    def create(self, request, post_id=None):
        try:
            post = Post.objects.get(id=post_id)  # Проверяем, существует ли публикация
        except Post.DoesNotExist:
            raise NotFound("Публикация не найдена.")  # Возвращаем ошибку, если публикация не найдена

        # Проверяем, аутентифицирован ли пользователь
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED  # Возвращаем ошибку 401, если пользователь не аутентифицирован
            )

        serializer = self.get_serializer(data=request.data)  # Создаем сериализатор с данными запроса
        serializer.is_valid(raise_exception=True)  # Проверяем валидность данных
        serializer.save(author=request.user, post=post)  # Сохраняем комментарий с автором и публикацией
        return Response(serializer.data, status=status.HTTP_201_CREATED)  # Возвращаем успешный ответ

    def retrieve(self, request, post_id=None, pk=None):
        try:
            comment = self.get_object()  # Получаем комментарий
        except Comment.DoesNotExist:
            raise NotFound("Комментарий не найден.")  # Возвращаем ошибку, если комментарий не найден

        serializer = self.get_serializer(comment)  # Сериализуем комментарий
        return Response(serializer.data)  # Возвращаем ответ с данными

    def partial_update(self, request, post_id=None, pk=None):
        comment = self.get_object()  # Получаем комментарий
        if comment.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужой комментарий."},
                status=status.HTTP_403_FORBIDDEN  # Возвращаем ошибку 403, если пользователь не автор комментария
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(
            comment, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, post_id=None, pk=None):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(
                {"detail": "Вы не можете удалить чужой комментарий."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
