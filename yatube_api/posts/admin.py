from django.contrib import admin
from .models import Group, Post, Comment, Follow

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description')  # Отображаем поля в админке

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'pub_date', 'group')  # Отображаем поля в админке
    ordering = ('-pub_date',)  # Сортировка по дате публикации по убыванию

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created')  # Отображаем поля в админке

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')  # Отображаем поля в админке