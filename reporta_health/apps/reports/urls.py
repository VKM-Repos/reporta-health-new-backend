"""
URL patterns for reports app
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report-list'),
    path('create/', views.ReportCreateView.as_view(), name='report-create'),
    path('my-reports/', views.UserReportsView.as_view(), name='user-reports'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('<int:pk>/status/', views.ReportStatusUpdateView.as_view(), name='report-status-update'),
    path('<int:report_id>/images/', views.ReportImageUploadView.as_view(), name='report-image-upload'),
]