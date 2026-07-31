"""
URL patterns for users app
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
    path('me/reviews/', views.UserReviewsView.as_view(), name='user-reviews'),
]