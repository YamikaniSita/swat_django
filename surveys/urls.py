from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
    path('create/', views.survey_create, name='survey_create'),
    path('<int:pk>/', views.survey_detail, name='survey_detail'),
    path('<int:pk>/edit/', views.survey_edit, name='survey_edit'),
    path('<int:pk>/delete/', views.survey_delete, name='survey_delete'),
    path('<int:pk>/responses/', views.survey_responses, name='survey_responses'),
    
    # Question URLs
    path('<int:survey_pk>/questions/create/', views.question_create, name='question_create'),
    path('<int:survey_pk>/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('<int:survey_pk>/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    
    # Template URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/questions/create/', views.template_question_create, name='template_question_create'),
    path('templates/<int:template_pk>/questions/<int:pk>/edit/', views.template_question_edit, name='template_question_edit'),
    path('templates/<int:template_pk>/questions/<int:pk>/delete/', views.template_question_delete, name='template_question_delete'),
    path('templates/<int:template_pk>/create-survey/', views.create_survey_from_template, name='create_survey_from_template'),
    
    # Social Media URLs
    path('<int:survey_pk>/social-media/', views.social_media_list, name='social_media_list'),
    path('<int:survey_pk>/social-media/create/', views.social_media_create, name='social_media_create'),
    path('social-media/<int:pk>/edit/', views.social_media_edit, name='social_media_edit'),
    path('social-media/<int:pk>/delete/', views.social_media_delete, name='social_media_delete'),
    path('survey/<int:pk>/start/', views.start_survey, name='start_survey'),
    path('sources/<int:pk>/edit/', views.source_edit, name='source_edit'),
] 