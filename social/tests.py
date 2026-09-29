from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Follow, Like, Post, Profile


class SocialPlatformTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='mira', password='StrongPass!72')
		self.other = User.objects.create_user(username='noah', password='StrongPass!72')
		self.post = Post.objects.create(author=self.user, content='A first thought.')

	def test_registration_creates_account_and_profile(self):
		response = self.client.post(reverse('register'), {
			'username': 'jules',
			'email': 'jules@example.com',
			'password1': 'StrongPass!72',
			'password2': 'StrongPass!72',
		})

		self.assertRedirects(response, reverse('home'))
		registered_user = User.objects.get(username='jules')
		self.assertTrue(Profile.objects.filter(user=registered_user).exists())
		self.assertEqual(int(self.client.session['_auth_user_id']), registered_user.pk)

	def test_invalid_registration_shows_validation_errors(self):
		response = self.client.post(reverse('register'), {
			'username': 'jules',
			'email': 'not-an-email',
			'password1': 'password',
			'password2': 'different',
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(username='jules').exists())
		self.assertTrue(response.context['form'].errors)

	def test_login_uses_django_authentication(self):
		response = self.client.post(reverse('login'), {
			'username': 'mira',
			'password': 'StrongPass!72',
		})

		self.assertRedirects(response, reverse('home'))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_feed_is_public_and_displays_posts(self):
		response = self.client.get(reverse('home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'A first thought.')
		self.assertContains(response, '@mira')

	def test_profile_displays_post_and_connection_counts(self):
		Follow.objects.create(follower=self.other, following=self.user)
		response = self.client.get(reverse('profile', args=['mira']))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'A first thought.')
		self.assertEqual(response.context['follower_count'], 1)
		self.assertEqual(response.context['following_count'], 0)

	def test_follower_and_following_pages_list_the_correct_users(self):
		Follow.objects.create(follower=self.other, following=self.user)
		Follow.objects.create(follower=self.user, following=User.objects.create_user(
			username='sage', password='StrongPass!72'
		))

		followers = self.client.get(reverse('connections', args=['mira', 'followers']))
		following = self.client.get(reverse('connections', args=['mira', 'following']))

		self.assertContains(followers, '@noah')
		self.assertNotContains(followers, '@sage')
		self.assertContains(following, '@sage')
		self.assertNotContains(following, '@noah')

	def test_login_and_post_detail_pages_render(self):
		self.assertEqual(self.client.get(reverse('login')).status_code, 200)
		response = self.client.get(reverse('post_detail', args=[self.post.pk]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'A first thought.')

	def test_edit_profile_requires_login_and_updates_details(self):
		self.assertRedirects(
			self.client.get(reverse('edit_profile')),
			f"{reverse('login')}?next={reverse('edit_profile')}",
		)
		self.client.force_login(self.user)
		response = self.client.post(reverse('edit_profile'), {
			'first_name': 'Mira',
			'last_name': 'Lane',
			'email': 'mira@example.com',
			'bio': 'A few words about me.',
			'location': 'Portland',
		})

		self.assertRedirects(response, reverse('profile', args=['mira']))
		self.user.refresh_from_db()
		self.assertEqual(self.user.first_name, 'Mira')
		self.assertEqual(self.user.profile.location, 'Portland')

	def test_authenticated_user_can_create_post(self):
		self.client.force_login(self.other)
		response = self.client.post(reverse('create_post'), {'content': 'A new post.'})

		self.assertRedirects(response, reverse('home'))
		self.assertTrue(Post.objects.filter(author=self.other, content='A new post.').exists())

	def test_post_edit_and_delete_are_limited_to_author(self):
		self.client.force_login(self.other)
		self.assertEqual(self.client.get(reverse('edit_post', args=[self.post.pk])).status_code, 404)
		self.assertEqual(self.client.post(reverse('delete_post', args=[self.post.pk])).status_code, 404)

		self.client.force_login(self.user)
		response = self.client.post(reverse('edit_post', args=[self.post.pk]), {
			'content': 'Updated thought.',
		})
		self.assertRedirects(response, reverse('post_detail', args=[self.post.pk]))
		self.post.refresh_from_db()
		self.assertEqual(self.post.content, 'Updated thought.')

		response = self.client.post(reverse('delete_post', args=[self.post.pk]))
		self.assertRedirects(response, reverse('home'))
		self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

	def test_comments_can_be_added_and_only_deleted_by_author(self):
		self.client.force_login(self.other)
		response = self.client.post(reverse('create_comment', args=[self.post.pk]), {
			'content': 'A useful reply.',
		})
		self.assertRedirects(response, reverse('home'))
		comment = Comment.objects.get(post=self.post)

		self.client.force_login(self.user)
		self.assertEqual(self.client.post(reverse('delete_comment', args=[comment.pk])).status_code, 404)
		self.client.force_login(self.other)
		response = self.client.post(reverse('delete_comment', args=[comment.pk]))
		self.assertRedirects(response, reverse('home'))
		self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

	def test_likes_toggle_without_duplicates_and_reject_external_redirect(self):
		self.client.force_login(self.other)
		response = self.client.post(reverse('toggle_like', args=[self.post.pk]), {
			'next': 'https://example.com/',
		})
		self.assertRedirects(response, reverse('home'))
		self.assertEqual(Like.objects.filter(user=self.other, post=self.post).count(), 1)

		self.client.post(reverse('toggle_like', args=[self.post.pk]))
		self.assertEqual(Like.objects.filter(user=self.other, post=self.post).count(), 0)

	def test_follow_toggle_counts_and_prevents_self_follow(self):
		self.client.force_login(self.user)
		response = self.client.post(reverse('toggle_follow', args=['noah']))
		self.assertRedirects(response, reverse('profile', args=['noah']))
		self.assertEqual(Follow.objects.filter(follower=self.user, following=self.other).count(), 1)

		self.client.post(reverse('toggle_follow', args=['noah']))
		self.assertFalse(Follow.objects.filter(follower=self.user, following=self.other).exists())

		self.client.post(reverse('toggle_follow', args=['mira']))
		self.assertFalse(Follow.objects.filter(follower=self.user, following=self.user).exists())

	def test_social_actions_require_login(self):
		response = self.client.post(reverse('toggle_like', args=[self.post.pk]))
		self.assertRedirects(
			response,
			f"{reverse('login')}?next={reverse('toggle_like', args=[self.post.pk])}",
		)
