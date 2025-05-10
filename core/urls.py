from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('surveys/<int:survey_id>/import/', views.import_responses, name='import_responses'),
    path('surveys/<int:survey_id>/export/', views.export_responses, name='export_responses'),
    path('surveys/<int:survey_id>/download-template/', views.download_template, name='download_template'),
    path('surveys/<int:survey_id>/report/', views.swot_analysis, name='swot_analysis'),
    path('volunteers/', views.manage_volunteers, name = "manage_volunteers"),
    path('surveys/<int:survey_id>/pdf_report/', views.report, name="report_pdf"),
] 