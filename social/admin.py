from django.contrib import admin
from .models import Comment, Follow, Like, Post, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'location', 'created_at')
	search_fields = ('user__username', 'location')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('author', 'created_at', 'updated_at')
	search_fields = ('author__username', 'content')
	list_filter = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('author', 'post', 'created_at')
	search_fields = ('author__username', 'content')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
	list_display = ('user', 'post', 'created_at')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
	list_display = ('follower', 'following', 'created_at')
