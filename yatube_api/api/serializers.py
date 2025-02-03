from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator  # Импортируем валидатор
from posts.models import Comment, Post, Follow, Group


class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Post
        fields = ['id', 'author', 'text', 'pub_date', 'image', 'group']
        read_only_fields = ['id', 'pub_date', 'author']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['group'] = instance.group.id if hasattr(instance, 'group') and instance.group else None
        return representation


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        fields = ['id', 'author', 'post', 'text', 'created']
        read_only_fields = ['author', 'post']
        model = Comment


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'slug', 'description']


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    following = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['user', 'following']
        # Добавляем валидатор для уникальности пары (user, following)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message="Вы уже подписаны на этого пользователя или не можете подписаться на себя."
            )
        ]

    def validate_following(self, value):
        # Проверяем, что пользователь не может подписаться на самого себя
        if self.context['request'].user == value:
            raise serializers.ValidationError("Вы не можете подписаться на себя.")
        return value
