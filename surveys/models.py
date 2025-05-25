from django.db import models
from django.utils import timezone

class SurveyResponse(models.Model):
    survey = models.ForeignKey('core.Survey', on_delete=models.CASCADE, related_name='survey_responses')
    volunteer = models.ForeignKey('core.Volunteers', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned')
    ], default='in_progress')

class SocialMediaSource(models.Model):
    survey = models.ForeignKey('core.Survey', on_delete=models.CASCADE, related_name='social_sources')
    platform = models.CharField(max_length=100, choices=[
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram')
    ])
    source_type = models.CharField(max_length=100, choices=[
        ('page', 'Page'),
        ('group', 'Group'),
        ('profile', 'Profile'),
        ('hashtag', 'Hashtag')
    ])
    required_data = models.CharField(max_length=20, choices=[
        ('all', 'All'),
        ('sentiment', 'Sentiment'),
        ('topics', 'Entities and Topics'),
    ], default='all')
    source_id = models.CharField(max_length=200, help_text="Page ID, Group ID, Profile username, or hashtag")
    source_name = models.CharField(max_length=255, help_text="Display name of the source")
    topics = models.TextField(help_text="Comma-separated list of topics to monitor")
    access_token = models.CharField(max_length=500, blank=True, null=True, help_text="Facebook Page Access Token (required for Facebook pages)")
    token_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the access token expires")
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    total_posts = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_reactions = models.IntegerField(default=0)
    total_pull_requests = models.IntegerField(default=0)
    successful_pull_requests = models.IntegerField(default=0)
    failed_pull_requests = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    indexed_posts = models.IntegerField(default=0)
    matching_posts = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source_name} ({self.platform})"

    def is_token_valid(self):
        if not self.token_expires_at:
            return True
        return timezone.now() < self.token_expires_at

    class Meta:
        unique_together = ['survey', 'platform', 'source_id']
        ordering = ['-started_at']

class QuestionResponse(models.Model):
    survey_response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='question_responses')
    question = models.ForeignKey('core.Question', on_delete=models.CASCADE)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response to {self.question.text[:30]}"

    class Meta:
        unique_together = ['survey_response', 'question']

class SurveyTemplate(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class TemplateQuestion(models.Model):
    template = models.ForeignKey(SurveyTemplate, on_delete=models.CASCADE, related_name='template_questions')
    text = models.TextField()
    swot_category = models.ForeignKey('core.SWOTCategory', on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.text[:50]}..."

    class Meta:
        ordering = ['order']
