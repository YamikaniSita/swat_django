from django.contrib import admin
from .models import Project, Location, SWOTCategory, Survey, Question, Response

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'start_date', 'status')
    list_filter = ('status', 'created_by', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'parent')
    list_filter = ('location_type', 'parent')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(SWOTCategory)
class SWOTCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name', 'description')

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'created_by', 'status', 'start_date')
    list_filter = ('status', 'project', 'created_by', 'start_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    filter_horizontal = ('target_locations',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'swot_category', 'order', 'is_required')
    list_filter = ('swot_category', 'is_required', 'survey')
    search_fields = ('text',)
    ordering = ('survey', 'order')

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'question', 'volunteer', 'sentiment_label', 'created_at')
    list_filter = ('sentiment_label', 'survey', 'question', 'created_at')
    search_fields = ('text', 'volunteer__name')
    date_hierarchy = 'created_at' 