# Generated by Django 5.1.7 on 2025-05-24 20:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('abandoned', 'Abandoned')], default='in_progress', max_length=20)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_responses', to='core.survey')),
                ('volunteer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.volunteers')),
            ],
        ),
        migrations.CreateModel(
            name='SurveyTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TemplateQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('order', models.IntegerField(default=0)),
                ('is_required', models.BooleanField(default=True)),
                ('swot_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.swotcategory')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_questions', to='surveys.surveytemplate')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='SocialMediaSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('facebook', 'Facebook'), ('twitter', 'Twitter'), ('linkedin', 'LinkedIn'), ('instagram', 'Instagram')], max_length=100)),
                ('source_type', models.CharField(choices=[('page', 'Page'), ('group', 'Group'), ('profile', 'Profile'), ('hashtag', 'Hashtag')], max_length=100)),
                ('required_data', models.CharField(choices=[('all', 'All'), ('sentiment', 'Sentiment'), ('topics', 'Entities and Topics')], default='all', max_length=20)),
                ('source_id', models.CharField(help_text='Page ID, Group ID, Profile username, or hashtag', max_length=200)),
                ('source_name', models.CharField(help_text='Display name of the source', max_length=255)),
                ('topics', models.TextField(help_text='Comma-separated list of topics to monitor')),
                ('access_token', models.CharField(blank=True, help_text='Facebook Page Access Token (required for Facebook pages)', max_length=500, null=True)),
                ('token_expires_at', models.DateTimeField(blank=True, help_text='When the access token expires', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('last_fetched', models.DateTimeField(blank=True, null=True)),
                ('total_posts', models.IntegerField(default=0)),
                ('total_comments', models.IntegerField(default=0)),
                ('total_reactions', models.IntegerField(default=0)),
                ('total_pull_requests', models.IntegerField(default=0)),
                ('successful_pull_requests', models.IntegerField(default=0)),
                ('failed_pull_requests', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True, null=True)),
                ('indexed_posts', models.IntegerField(default=0)),
                ('matching_posts', models.IntegerField(default=0)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_sources', to='core.survey')),
            ],
            options={
                'ordering': ['-started_at'],
                'unique_together': {('survey', 'platform', 'source_id')},
            },
        ),
        migrations.CreateModel(
            name='QuestionResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.question')),
                ('survey_response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_responses', to='surveys.surveyresponse')),
            ],
            options={
                'unique_together': {('survey_response', 'question')},
            },
        ),
    ]
