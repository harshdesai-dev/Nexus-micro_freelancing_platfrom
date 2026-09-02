from django.urls import path

from accounts.views import login_view, logout_view, me_view, register_view

urlpatterns = [
    path('auth/register', register_view, name='register'),
    path('auth/login', login_view, name='login'),
    path('auth/logout', logout_view, name='logout'),
    path('users/me', me_view, name='current-user'),
]
