from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Comment, Post, Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


class UserDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'What would you like to share?',
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Write a comment...'}),
        }