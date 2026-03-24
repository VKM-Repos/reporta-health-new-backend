"""
URL patterns for users app
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('me/reviews/', views.UserReviewsView.as_view(), name='user-reviews'),
]