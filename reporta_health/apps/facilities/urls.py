"""
URL patterns for facilities app
"""

from django.urls import path
from . import views
from apps.reviews import views as review_views

app_name = 'facilities'

urlpatterns = [
    path('', views.FacilityListView.as_view(), name='facility-list'),
    path('nearby/', views.nearby_facilities, name='nearby-facilities'),
    path('<int:pk>/', views.FacilityDetailView.as_view(), name='facility-detail'),
    path('create/', views.FacilityCreateView.as_view(), name='facility-create'),
    path('<int:pk>/update/', views.FacilityUpdateView.as_view(), name='facility-update'),
    path('<int:pk>/delete/', views.FacilityDeleteView.as_view(), name='facility-delete'),
    path('<int:facility_id>/images/', views.FacilityImageUploadView.as_view(), name='facility-image-upload'),
    path('<int:facility_id>/reviews/create/', review_views.ReviewCreateView.as_view(), name='facility-review-create'),
    path('<int:facility_id>/reviews/', review_views.FacilityReviewListView.as_view(), name='facility-reviews'),
]