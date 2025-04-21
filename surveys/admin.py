from django.contrib import admin
from .models import SurveyResponse, QuestionResponse, SurveyTemplate, TemplateQuestion

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'volunteer', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'survey', 'volunteer', 'started_at')
    search_fields = ('volunteer__name', 'survey__title')
    date_hierarchy = 'started_at'

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ('survey_response', 'question', 'created_at')
    list_filter = ('survey_response__survey', 'created_at')
    search_fields = ('answer', 'question__text')
    date_hierarchy = 'created_at'

@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_by', 'created_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

@admin.register(TemplateQuestion)
class TemplateQuestionAdmin(admin.ModelAdmin):
    list_display = ('template', 'text', 'swot_category', 'order', 'is_required')
    list_filter = ('swot_category', 'is_required', 'template')
    search_fields = ('text',)
    ordering = ('template', 'order') 