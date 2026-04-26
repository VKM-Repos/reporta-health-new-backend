"""
URL patterns for facilities app
"""

from django.urls import path
from . import views
from . import analytics_views   
from apps.reviews import views as review_views

app_name = 'facilities'

urlpatterns = [
    path('types/', views.FacilityTypesView.as_view(), name='facility-types'),
    path('states/', views.FacilityStatesView.as_view(), name='facility-states'),
    path('', views.FacilityListView.as_view(), name='facility-list'),
    path('nearby/', views.nearby_facilities, name='nearby-facilities'),
    path('<int:pk>/', views.FacilityDetailView.as_view(), name='facility-detail'),
    path('create/', views.FacilityCreateView.as_view(), name='facility-create'),
    path('<int:pk>/update/', views.FacilityUpdateView.as_view(), name='facility-update'),
    path('<int:pk>/delete/', views.FacilityDeleteView.as_view(), name='facility-delete'),
    path('<int:facility_id>/images/', views.FacilityImageUploadView.as_view(), name='facility-image-upload'),
    path('<int:facility_id>/reviews/create/', review_views.ReviewCreateView.as_view(), name='facility-review-create'),
    path('<int:facility_id>/reviews/', review_views.FacilityReviewListView.as_view(), name='facility-reviews'),

    # ── analytics ─────────────────────────────────────────────────────────
    path('stats/by-state/', analytics_views.FacilityStatsByAllStatesView.as_view(), name='stats-all-states'),
    path('stats/by-lga/', analytics_views.FacilityStatsByAllLGAsView.as_view(), name='stats-all-lgas'),
    path('stats/by-state/<str:state>/', analytics_views.FacilityStatsByStateView.as_view(), name='stats-by-state'),
    path('stats/by-state/<str:state>/ownership/', analytics_views.FacilityStatsByStateOwnershipView.as_view(), name='stats-state-ownership'),
    path('stats/by-state/<str:state>/care-level/', analytics_views.FacilityStatsByStateCareLevelView.as_view(), name='stats-state-care-level'),
    path('stats/by-state/<str:state>/lgas/', analytics_views.FacilityStatsByLGAsInStateView.as_view(), name='stats-lgas-in-state'),
    path('stats/by-state/<str:state>/lgas/<str:lga>/', analytics_views.FacilityStatsByLGAView.as_view(), name='stats-by-lga'),
]