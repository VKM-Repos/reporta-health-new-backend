"""
URL patterns for reviews app
"""

from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('<int:pk>/update/', views.ReviewUpdateView.as_view(), name='review-update'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review-delete'),
    path('<int:review_id>/images/', views.ReviewImageUploadView.as_view(), name='review-image-upload'),
]

# Note: Facility-specific review endpoints are in facilities/urls.py