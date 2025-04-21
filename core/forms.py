from django import forms
from .models import Project, Question, SWOTCategory

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'location', 'start_date', 'end_date', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'swot_category', 'order', 'is_required']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 1}),
        }
        help_texts = {
            'text': 'Enter the question text that aligns with the selected SWOT category.',
            'swot_category': 'Select the SWOT category this question belongs to.',
            'order': 'Specify the order in which this question should appear in the survey.',
            'is_required': 'Check if this question must be answered.',
        } 