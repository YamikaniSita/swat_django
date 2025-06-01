from django import forms
from django.utils import timezone
from .models import SocialMediaSource, SurveyTemplate, SurveyResponse, TemplateQuestion
from core.models import Survey, Question
from core.models import Project, SWOTCategory
from datetime import datetime

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['project', 'title', 'description', 'start_date', 'end_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        help_texts = {
            'project': 'Select the project this survey belongs to.',
            'title': 'Enter a descriptive title for your survey.',
            'description': 'Provide a brief description of what this survey is about.',
            'start_date': 'Select when this survey should start.',
            'end_date': 'Select when this survey should end (optional).',
            'status': 'Set the initial status of the survey.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = Project.objects.filter(created_by=user)
        
        # Set minimum date to today for start_date
        today = timezone.now().date()
        self.fields['start_date'].widget.attrs['min'] = today.isoformat()
        
        # Set minimum date to start_date for end_date
        if self.instance.pk and self.instance.start_date:
            self.fields['end_date'].widget.attrs['min'] = self.instance.start_date.date().isoformat()
        else:
            self.fields['end_date'].widget.attrs['min'] = today.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Convert dates to datetime
        if start_date:
            cleaned_data['start_date'] = timezone.make_aware(
                datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            cleaned_data['end_date'] = timezone.make_aware(
                datetime.combine(end_date, datetime.max.time())
            )
        
        # If no end date is provided, set it to start date
        if start_date and not end_date:
            cleaned_data['end_date'] = timezone.make_aware(
                datetime.combine(start_date, datetime.max.time())
            )
        
        return cleaned_data

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            # Convert to datetime for comparison
            start_datetime = timezone.make_aware(
                datetime.combine(start_date, datetime.min.time())
            )
            if start_datetime < timezone.now():
                raise forms.ValidationError("Start date cannot be in the past.")
            return start_date
        return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if start_date and end_date:
            # Convert to datetime for comparison
            start_datetime = timezone.make_aware(
                datetime.combine(start_date, datetime.min.time())
            )
            end_datetime = timezone.make_aware(
                datetime.combine(end_date, datetime.max.time())
            )
            if end_datetime < start_datetime:
                raise forms.ValidationError("End date must be after start date.")
            return end_date
        return end_date

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'swot_category', 'order', 'is_required', 'required_data']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'swot_category': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'text': 'Enter the question text.',
            'swot_category': 'Select the SWOT category this question belongs to.',
            'order': 'Set the order in which this question appears (optional).',
            'is_required': 'Check if this question is mandatory.',
        }

class SocialMediaSourceForm(forms.ModelForm):
    class Meta:
        model = SocialMediaSource
        fields = ['platform', 'source_type', 'source_id', 'source_name', 'required_data', 'topics', 'access_token']
        widgets = {
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'source_id': forms.TextInput(attrs={'class': 'form-control'}),
            'source_name': forms.TextInput(attrs={'class': 'form-control'}),
            'required_date': forms.TextInput(attrs={'class': 'form-control'}),
            'topics': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter topics separated by commas'}),
            'access_token': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Facebook Page Access Token'})
        }
        help_texts = {
            'platform': 'Select the social media platform',
            'source_type': 'Select the type of source (page, group, profile, or hashtag)',
            'source_id': 'Enter the page ID, group ID, username, or hashtag',
            'source_name': 'Enter a display name for this source',
            'topics': 'Enter the topics you want to monitor (comma-separated)',
            'access_token': 'Required for Facebook pages. Get this from your Facebook Page settings.'
        }

    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey', None)
        super().__init__(*args, **kwargs)
        if survey:
            self.instance.survey = survey

    def clean(self):
        cleaned_data = super().clean()
        platform = cleaned_data.get('platform')
        source_type = cleaned_data.get('source_type')
        access_token = cleaned_data.get('access_token')

        # Require access token for Facebook pages
        if platform == 'facebook' and source_type == 'page' and not access_token:
            self.add_error('access_token', 'Access token is required for Facebook pages')

        return cleaned_data

    def clean_access_token(self):
        access_token = self.cleaned_data.get('access_token')
        if access_token:
            # Basic validation - check if token is not empty
            if not access_token.strip():
                raise forms.ValidationError("Access token cannot be empty")
        return access_token

class SurveyTemplateForm(forms.ModelForm):
    class Meta:
        model = SurveyTemplate
        fields = ['title', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TemplateQuestionForm(forms.ModelForm):
    class Meta:
        model = TemplateQuestion
        fields = ['text', 'swot_category', 'order', 'is_required']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 0}),
        } 