from django.conf import settings
from django.db import models
from django.urls import reverse


class Profile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='profile',
	)
	bio = models.TextField(max_length=500, blank=True)
	location = models.CharField(max_length=100, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.user.username} profile'


class Post(models.Model):
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='posts',
	)
	content = models.TextField(max_length=2000)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.author.username}: {self.content[:40]}'

	def get_absolute_url(self):
		return reverse('post_detail', kwargs={'pk': self.pk})


class Comment(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
	author = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='comments',
	)
	content = models.CharField(max_length=500)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f'Comment by {self.author.username} on post {self.post_id}'


class Like(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='likes',
	)
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_like'),
		]

	def __str__(self):
		return f'{self.user.username} likes post {self.post_id}'


class Follow(models.Model):
	follower = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='following_relations',
	)
	following = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='follower_relations',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=['follower', 'following'],
				name='unique_follower_following',
			),
			models.CheckConstraint(
				condition=~models.Q(follower=models.F('following')),
				name='prevent_self_follow',
			),
		]

	def __str__(self):
		return f'{self.follower.username} follows {self.following.username}'
