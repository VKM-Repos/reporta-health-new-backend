"""
Main URL Configuration for Reporta Health
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers
from apps.users.views import ThrottledTokenObtainPairView, ThrottledTokenRefreshView

# API Router
router = routers.DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    

    path('api/auth/jwt/create/', ThrottledTokenObtainPairView.as_view(), name='jwt-create'),
    path('api/auth/jwt/refresh/', ThrottledTokenRefreshView.as_view(), name='jwt-refresh'),

    # Authentication (Djoser)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    
    # App URLs
    path('api/', include(router.urls)),
    path('api/users/', include('apps.users.urls')),
    path('api/facilities/', include('apps.facilities.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Customize admin site
admin.site.site_header = "Reporta Health Admin"
admin.site.site_title = "Reporta Health"
admin.site.index_title = "Welcome to Reporta Health Admin Panel"