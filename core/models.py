from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ], default='planning')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class Location(models.Model):
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=[
        ('national', 'National'),
        ('regional', 'Regional'),
        ('district', 'District'),
        ('constituency', 'Constituency')
    ])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"

    class Meta:
        ordering = ['name']

class SWOTCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    color = models.CharField(max_length=7, default='#000000')  # For UI visualization

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "SWOT Categories"

class Survey(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='surveys')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ], default='draft')
    target_locations = models.ManyToManyField(Location, related_name='surveys')

    def __str__(self):
        return f"{self.title} - {self.project.name}"

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    swot_category = models.ForeignKey(SWOTCategory, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    required_data = models.CharField(max_length=20, choices=[
        ('all', 'All'),
        ('sentiment', 'Sentiment'),
        ('topics', 'Entities and Topics'),
    ], default='all')

    def __str__(self):
        return f"{self.text[:50]}..."

    class Meta:
        ordering = ['order']

class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    volunteer = models.ForeignKey('core.Volunteers', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    translated_from = models.TextField(default="")
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.question.text[:30]}..."

    class Meta:
        ordering = ['-created_at']

class SocialMediaResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='social_responses')
    source_type = models.CharField(max_length=20, choices=[
        ('facebook', 'Facebook'),
        ('facebook_comment', 'Facebook Comment'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram')
    ])
    source_id = models.CharField(max_length=100)  # Original post ID from the platform
    text = models.TextField() 
    translated_from = models.TextField(null=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], null=True, blank=True)
    topics = models.JSONField(default=list)
    entities = models.JSONField(default=list)
    created_at = models.DateTimeField()
    social_source = models.ForeignKey('surveys.SocialMediaSource', on_delete=models.CASCADE, null=False)
    


    def __str__(self):
        return f"{self.source_type} post from {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['survey', 'source_id'] 

class Volunteers(models.Model):
    name = models.TextField()
    phone_number = models.CharField(max_length=15, unique=True)
    sex = models.CharField(max_length=2)
    birthdate = models.DateTimeField(blank=True)
    region = models.TextField()
    location_id = models.ForeignKey(Location, null=False, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} volunteer {self.created_at}"
    
