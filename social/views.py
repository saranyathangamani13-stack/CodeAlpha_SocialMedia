from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm, ProfileForm, RegisterForm, UserDetailsForm
from .models import Comment, Follow, Like, Post, Profile


def home(request):
	posts = Post.objects.select_related('author').prefetch_related(
		'comments__author', 'likes'
	)
	liked_post_ids = set()
	if request.user.is_authenticated:
		liked_post_ids = set(request.user.likes.values_list('post_id', flat=True))
	return render(request, 'social/home.html', {
		'posts': posts,
		'liked_post_ids': liked_post_ids,
		'comment_form': CommentForm(),
		'post_form': PostForm(),
	})


def register(request):
	if request.user.is_authenticated:
		return redirect('home')
	form = RegisterForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		Profile.objects.create(user=user)
		login(request, user)
		messages.success(request, 'Your account is ready. Welcome!')
		return redirect('home')
	return render(request, 'social/register.html', {'form': form})


def profile(request, username):
	profile_user = get_object_or_404(User, username=username)
	user_profile, _ = Profile.objects.get_or_create(user=profile_user)
	is_following = request.user.is_authenticated and Follow.objects.filter(
		follower=request.user, following=profile_user
	).exists()
	return render(request, 'social/profile.html', {
		'profile_user': profile_user,
		'profile': user_profile,
		'posts': profile_user.posts.select_related('author').prefetch_related('likes'),
		'follower_count': profile_user.follower_relations.count(),
		'following_count': profile_user.following_relations.count(),
		'is_following': is_following,
		'liked_post_ids': set(request.user.likes.values_list('post_id', flat=True))
		if request.user.is_authenticated else set(),
	})


@login_required
def edit_profile(request):
	profile, _ = Profile.objects.get_or_create(user=request.user)
	user_form = UserDetailsForm(request.POST or None, instance=request.user)
	profile_form = ProfileForm(request.POST or None, instance=profile)
	if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
		user_form.save()
		profile_form.save()
		messages.success(request, 'Your profile has been updated.')
		return redirect('profile', username=request.user.username)
	return render(request, 'social/edit_profile.html', {
		'user_form': user_form,
		'profile_form': profile_form,
	})


@login_required
def create_post(request):
	form = PostForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		post = form.save(commit=False)
		post.author = request.user
		post.save()
		messages.success(request, 'Your post has been published.')
		return redirect('home')
	return render(request, 'social/create_post.html', {'form': form})


@login_required
def edit_post(request, pk):
	post = get_object_or_404(Post, pk=pk, author=request.user)
	form = PostForm(request.POST or None, instance=post)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Your post has been updated.')
		return redirect('post_detail', pk=post.pk)
	return render(request, 'social/edit_post.html', {'form': form, 'post': post})


@login_required
@require_POST
def delete_post(request, pk):
	post = get_object_or_404(Post, pk=pk, author=request.user)
	post.delete()
	messages.success(request, 'Your post has been deleted.')
	return redirect('home')


def post_detail(request, pk):
	post = get_object_or_404(
		Post.objects.select_related('author').prefetch_related('comments__author', 'likes'),
		pk=pk,
	)
	liked = request.user.is_authenticated and Like.objects.filter(
		user=request.user, post=post
	).exists()
	return render(request, 'social/post_detail.html', {
		'post': post,
		'liked': liked,
		'comment_form': CommentForm(),
	})


@login_required
@require_POST
def create_comment(request, pk):
	post = get_object_or_404(Post, pk=pk)
	form = CommentForm(request.POST)
	if form.is_valid():
		comment = form.save(commit=False)
		comment.post = post
		comment.author = request.user
		comment.save()
		messages.success(request, 'Your comment has been added.')
	else:
		messages.error(request, 'Comments must contain 1 to 500 characters.')
	return redirect('post_detail' if request.POST.get('return_to_detail') else 'home', **(
		{'pk': post.pk} if request.POST.get('return_to_detail') else {}
	))


@login_required
@require_POST
def delete_comment(request, pk):
	comment = get_object_or_404(Comment, pk=pk, author=request.user)
	post_id = comment.post_id
	comment.delete()
	messages.success(request, 'Your comment has been deleted.')
	if request.POST.get('return_to_detail'):
		return redirect('post_detail', pk=post_id)
	return redirect('home')


@login_required
@require_POST
def toggle_like(request, pk):
	post = get_object_or_404(Post, pk=pk)
	like, created = Like.objects.get_or_create(user=request.user, post=post)
	if not created:
		like.delete()
	next_url = request.POST.get('next')
	if next_url and url_has_allowed_host_and_scheme(
		next_url,
		allowed_hosts={request.get_host()},
		require_https=request.is_secure(),
	):
		return redirect(next_url)
	return redirect('home')


@login_required
@require_POST
def toggle_follow(request, username):
	target = get_object_or_404(User, username=username)
	if target == request.user:
		messages.error(request, 'You cannot follow yourself.')
	else:
		relation, created = Follow.objects.get_or_create(
			follower=request.user,
			following=target,
		)
		if created:
			messages.success(request, f'You are now following {target.username}.')
		else:
			relation.delete()
			messages.success(request, f'You unfollowed {target.username}.')
	return redirect('profile', username=target.username)


def connections(request, username, connection_type):
	if connection_type not in ('followers', 'following'):
		from django.http import Http404
		raise Http404
	profile_user = get_object_or_404(User, username=username)
	if connection_type == 'followers':
		users = User.objects.filter(following_relations__following=profile_user)
		title = f"People following {profile_user.username}"
	else:
		users = User.objects.filter(follower_relations__follower=profile_user)
		title = f"People {profile_user.username} follows"
	return render(request, 'social/connections.html', {
		'profile_user': profile_user,
		'users': users.distinct().order_by('username'),
		'title': title,
	})
