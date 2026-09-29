from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='social/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('profile/<str:username>/<str:connection_type>/', views.connections, name='connections'),
    path('posts/create/', views.create_post, name='create_post'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:pk>/comment/', views.create_comment, name='create_comment'),
    path('posts/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('comments/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]