from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .pagination import PostPagination
from posts.models import Post, Follow, Comment, Group
from . import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound
from .permissions import IsAuthorOrReadOnly, IsFollowing


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        self.pagination_class = None
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer
    pagination_class = PostPagination
    permission_classes = [IsAuthorOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def update(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {"detail": "Вы не можете удалить чужую публикацию."},
                status=status.HTTP_403_FORBIDDEN
            )
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    permission_classes = [IsAuthorOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)

    def list(self, request, post_id=None):
        try:
            Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("Публикация не найдена.")

        comments = self.get_queryset()
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)

    def create(self, request, post_id=None):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("Публикация не найдена.")

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, post_id=None, pk=None):
        try:
            comment = self.get_object()
        except Comment.DoesNotExist:
            raise NotFound("Комментарий не найден.")

        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    def partial_update(self, request, post_id=None, pk=None):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(
                {"detail": "Вы не можете изменить чужой комментарий."},
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


class FollowViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.FollowSerializer
    # Объединяем permission_classes в один список
    permission_classes = [permissions.IsAuthenticated, IsFollowing]  # Изменено

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', None)
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(following__username__icontains=search)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        following_username = request.data.get('following')
        if not following_username:
            return Response(
                {"following": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        if following_username == request.user.username:
            return Response(
                {"error": "Вы не можете подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            following_user = User.objects.get(username=following_username)
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        if Follow.objects.filter(
            user=request.user, following=following_user
        ).exists():
            return Response(
                {"error": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(
            user=request.user, following=following_user
        )

        return Response(
            {
                "user": request.user.username,
                "following": following_user.username
            },
            status=status.HTTP_201_CREATED
        )
# Удалены ненужные методы (retrieve, partial_update, destroy) для соответствия требованиям
