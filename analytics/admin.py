from django.contrib import admin
from .models import SentimentAnalysis, TopicAnalysis, NamedEntity, ProjectReport

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('response', 'score', 'label', 'confidence', 'analyzed_at')
    list_filter = ('label', 'analyzed_at')
    search_fields = ('response__text',)
    date_hierarchy = 'analyzed_at'

@admin.register(TopicAnalysis)
class TopicAnalysisAdmin(admin.ModelAdmin):
    list_display = ('survey', 'topic', 'weight', 'analyzed_at')
    list_filter = ('survey', 'analyzed_at')
    search_fields = ('topic', 'survey__title')
    date_hierarchy = 'analyzed_at'

@admin.register(NamedEntity)
class NamedEntityAdmin(admin.ModelAdmin):
    list_display = ('text', 'entity_type', 'confidence', 'extracted_at')
    list_filter = ('entity_type', 'extracted_at')
    search_fields = ('text', 'response__text')
    date_hierarchy = 'extracted_at'

@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'created_by', 'report_type', 'created_at')
    list_filter = ('report_type', 'project', 'created_by', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at' 