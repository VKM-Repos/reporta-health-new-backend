"""
URL patterns for GBV app.
"""
from django.urls import path
from . import views

app_name = 'gbv'

urlpatterns = [
    path('nearby/',            views.GBVNearbyView.as_view(),        name='gbv-nearby'),
    path('services/',          views.GBVServiceListView.as_view(),   name='gbv-service-list'),
    path('services/nearby/',   views.GBVServiceNearbyView.as_view(), name='gbv-service-nearby'),
]