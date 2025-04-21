from django.db import models
from core.models import Project, Survey, Response
from django.contrib.auth.models import User

class SentimentAnalysis(models.Model):
    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='sentiment_analysis')
    score = models.FloatField()
    label = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ])
    confidence = models.FloatField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sentiment Analysis for {self.response}"

class TopicAnalysis(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='topic_analyses')
    topic = models.CharField(max_length=100)
    weight = models.FloatField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Topic: {self.topic} in {self.survey}"

class NamedEntity(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='named_entities')
    text = models.CharField(max_length=200)
    entity_type = models.CharField(max_length=50, choices=[
        ('person', 'Person'),
        ('organization', 'Organization'),
        ('location', 'Location'),
        ('date', 'Date'),
        ('other', 'Other')
    ])
    confidence = models.FloatField()
    extracted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text} ({self.get_entity_type_display()})"

class ProjectReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    report_type = models.CharField(max_length=50, choices=[
        ('sentiment', 'Sentiment Analysis'),
        ('topic', 'Topic Analysis'),
        ('entity', 'Entity Analysis'),
        ('summary', 'Summary Report')
    ])
    data = models.JSONField(null=True, blank=True)  # For storing additional report data

    def __str__(self):
        return f"{self.title} - {self.project.name}"

    class Meta:
        ordering = ['-created_at'] 