from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('sentiment/', views.sentiment_analysis, name='sentiment_analysis'),
    path('topics/', views.topic_analysis, name='topic_analysis'),
    path('entities/', views.named_entity_analysis, name='named_entity_analysis'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/download/', views.report_download, name='report_download'),
] 