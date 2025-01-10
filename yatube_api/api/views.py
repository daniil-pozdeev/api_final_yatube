from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .pagination import PostPagination
from posts.models import Post, Follow, Comment, Group
from . import serializers
from django.contrib.auth.models import User


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()  # Получаем все посты
    # Указываем сериализатор
    serializer_class = serializers.PostSerializer  
    # Указываем класс пагинации
    pagination_class = PostPagination  

    def get_permissions(self):
        # Устанавливаем права доступа в зависимости от действия
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]  # Доступ для всех
        # Доступ только для аутентифицированных пользователей
        return [permissions.IsAuthenticated()]  

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # Получаем queryset
        page = self.paginate_queryset(queryset)  # Пагинация
        if page is not None:
            # Сериализация данных
            serializer = self.get_serializer(page, many=True)  
            # Возвращаем пагинированный ответ
            return self.get_paginated_response(serializer.data)  

        # Сериализация всех данных
        serializer = self.get_serializer(queryset, many=True)  
        return Response(serializer.data)  # Возвращаем ответ

    def create(self, request, *args, **kwargs):
        # Получаем данные из запроса
        serializer = self.get_serializer(data=request.data)  
        # Проверяем валидность данных
        serializer.is_valid(raise_exception=True)  
        serializer.save(author=request.user)  # Сохраняем пост с автором
        # Возвращаем созданный пост
        return Response(serializer.data, status=status.HTTP_201_CREATED)  

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()  # Получаем конкретный пост
        serializer = self.get_serializer(post)  # Сериализация поста
        return Response(serializer.data)  # Возвращаем данные поста

    def partial_update(self, request, pk=None):
        post = self.get_object()  # Получаем пост для частичного обновления
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                # Запрещаем изменение чужого поста
                status=status.HTTP_403_FORBIDDEN  
            )
        # Сериализация с частичными данными
        serializer = self.get_serializer(post, data=request.data, partial=True)  
        # Проверяем валидность
        serializer.is_valid(raise_exception=True)  
        serializer.save()  # Сохраняем изменения
        # Возвращаем обновленные данные
        return Response(serializer.data)  

    def update(self, request, pk=None):
        # Получаем пост для полного обновления
        post = self.get_object()  
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                # Запрещаем изменение чужого поста
                status=status.HTTP_403_FORBIDDEN  
            )
        # Сериализация с новыми данными
        serializer = self.get_serializer(post, data=request.data)  
        # Проверяем валидность
        serializer.is_valid(raise_exception=True)  
        serializer.save()  # Сохраняем изменения
        # Возвращаем обновленные данные
        return Response(serializer.data)  

    def destroy(self, request, pk=None):
        post = self.get_object()  # Получаем пост для удаления
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете удалить чужую публикацию."},
                # Запрещаем удаление чужого поста
                status=status.HTTP_403_FORBIDDEN  
            )
        post.delete()  # Удаляем пост
        # Возвращаем статус 204 - нет содержимого
        return Response(status=status.HTTP_204_NO_CONTENT)  


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()  # Получаем все группы
    # Указываем сериализатор
    serializer_class = serializers.GroupSerializer  
    # Разрешаем доступ всем пользователям
    permission_classes = [permissions.AllowAny]  

    def list(self, request, *args, **kwargs):
        self.pagination_class = None  # Отключаем пагинацию
        # Вызываем родительский метод
        return super().list(request, *args, **kwargs)  

    def retrieve(self, request, *args, **kwargs):
        # Вызываем родительский метод
        return super().retrieve(request, *args, **kwargs)  


class FollowViewSet(viewsets.GenericViewSet):
    # Указываем сериализатор
    serializer_class = serializers.FollowSerializer  
    # Доступ только для аутентифицированных пользователей
    permission_classes = [permissions.IsAuthenticated]  

    def get_queryset(self):
        # Фильтруем подписки по текущему пользователю
        return Follow.objects.filter(user=self.request.user)  

    def list(self, request, *args, **kwargs):
        # Получаем параметр поиска
        search = request.query_params.get('search', None)  
        queryset = self.get_queryset()  # Получаем базовый queryset
        if search:
            # Фильтруем подписки по имени пользователя
            queryset = queryset.filter(following__username__icontains=search)
            # Сериализуем данные
        serializer = self.get_serializer(queryset, many=True)  
        # Возвращаем ответ с данными
        return Response(serializer.data)  

    def create(self, request, *args, **kwargs):
        # Получаем имя пользователя, на которого подписываемся
        following_username = request.data.get('following')  
        if not following_username:
            return Response(
                {"following": ["Обязательное поле."]},
                # Возвращаем ошибку, если поле пустое
                status=status.HTTP_400_BAD_REQUEST  
            )

        if following_username == request.user.username:
            return Response(
                {"error": "Вы не можете подписаться на себя."},
                # Возвращаем ошибку, если пользователь пытается подписаться на себя
                status=status.HTTP_400_BAD_REQUEST  
            )

        try:
            # Ищем пользователя по имени
            following_user = User.objects.get(username=following_username)  
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден."},
                # Возвращаем ошибку, если пользователь не найден
                status=status.HTTP_404_NOT_FOUND  
            )

        if Follow.objects.filter(user=request.user,
                                 following=following_user).exists():
            return Response(
                {"error": "Вы уже подписаны на этого пользователя."},
                # Возвращаем ошибку, если подписка уже существует
                status=status.HTTP_400_BAD_REQUEST  
            )

        # Создаем новую подписку
        Follow.objects.create(user=request.user, following=following_user)

        return Response(
            {
                "user": request.user.username,
                "following": following_user.username
            },
            # Возвращаем успешный ответ
            status=status.HTTP_201_CREATED  
        )


class CommentViewSet(viewsets.ModelViewSet):
    # Указываем сериализатор для комментариев
    serializer_class = serializers.CommentSerializer  
    # Доступ только для аутентифицированных пользователей
    permission_classes = [permissions.IsAuthenticated]  

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Разрешаем доступ всем
            permission_classes = [permissions.AllowAny]  
        else:
            # Остальные действия требуют аутентификации
            permission_classes = [permissions.IsAuthenticated]  
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Получаем ID публикации из URL
        post_id = self.kwargs['post_id']  
        # Фильтруем комментарии по ID публикации
        return Comment.objects.filter(post_id=post_id)  

    def list(self, request, post_id=None):
        try:
            # Проверяем, существует ли публикация
            Post.objects.get(id=post_id)  
        except Post.DoesNotExist:
            # Возвращаем ошибку, если публикация не найдена
            raise NotFound("Публикация не найдена.")  

        comments = self.get_queryset()  # Получаем комментарии
        # Сериализуем данные
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)  # Возвращаем ответ с данными

    def create(self, request, post_id=None):
        try:
            # Проверяем, существует ли публикация
            post = Post.objects.get(id=post_id)  
        except Post.DoesNotExist:
            # Возвращаем ошибку, если публикация не найдена
            raise NotFound("Публикация не найдена.")  

        # Проверяем, аутентифицирован ли пользователь
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                # Возвращаем ошибку 401, если пользователь не аутентифицирован
                status=status.HTTP_401_UNAUTHORIZED  
            )

        # Создаем сериализатор с данными запроса
        serializer = self.get_serializer(data=request.data)  
        # Проверяем валидность данных
        serializer.is_valid(raise_exception=True)  
        # Сохраняем комментарий с автором и публикацией
        serializer.save(author=request.user, post=post)  
        # Возвращаем успешный ответ
        return Response(serializer.data, status=status.HTTP_201_CREATED)  

    def retrieve(self, request, post_id=None, pk=None):
        try:
            comment = self.get_object()  # Получаем комментарий
        except Comment.DoesNotExist:
            # Возвращаем ошибку, если комментарий не найден
            raise NotFound("Комментарий не найден.")  

        serializer = self.get_serializer(comment)  # Сериализуем комментарий
        return Response(serializer.data)  # Возвращаем ответ с данными

    def partial_update(self, request, post_id=None, pk=None):
        comment = self.get_object()  # Получаем комментарий
        if comment.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужой комментарий."},
                # Возвращаем ошибку 403, если пользователь не автор комментария
                status=status.HTTP_403_FORBIDDEN  
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
