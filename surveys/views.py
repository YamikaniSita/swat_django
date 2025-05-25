from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import SocialMediaSource, SurveyTemplate, SurveyResponse, TemplateQuestion
from core.models import Survey, Question
from core.models import Project, Response, SocialMediaResponse
from core.analytics import analyze_survey_responses
from .forms import SurveyForm, QuestionForm, SurveyTemplateForm, TemplateQuestionForm, SocialMediaSourceForm
from .services import start_survey_collection

@login_required
def survey_list(request):
    """List all surveys."""
    surveys = Survey.objects.filter(project__created_by=request.user).order_by('-created_at')
    return render(request, 'surveys/survey_list.html', {'surveys': surveys})

@login_required
def survey_create(request):
    """Create a new survey."""
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.created_by = request.user
            survey.save()
            messages.success(request, 'Survey created successfully.')
            return redirect('surveys:survey_detail', pk=survey.pk)
    else:
        form = SurveyForm()
        if 'project' in request.GET:
            form.fields['project'].initial = request.GET.get('project')
    
    return render(request, 'surveys/survey_form.html', {'form': form})

@login_required
def survey_detail(request, pk):
    """View survey details."""
    survey = get_object_or_404(Survey, pk=pk, project__created_by=request.user)
    responses = Response.objects.filter(survey=survey).select_related('question')
    social_responses = SocialMediaResponse.objects.filter(survey=survey)
    
    # Get analytics including word map
    analytics = analyze_survey_responses(list(responses) + list(social_responses))
    print(analytics)
    context = {
        'survey': survey,
        'responses': responses,
        'social_responses': social_responses,
        'analytics': analytics,
    }
    return render(request, 'surveys/survey_detail.html', context)

@login_required
def survey_edit(request, pk):
    """Edit a survey."""
    survey = get_object_or_404(Survey, pk=pk, project__created_by=request.user)
    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Survey updated successfully.')
            return redirect('surveys:survey_detail', pk=survey.pk)
    else:
        form = SurveyForm(instance=survey)
    
    return render(request, 'surveys/survey_form.html', {'form': form, 'survey': survey})

@login_required
def survey_delete(request, pk):
    """Delete a survey."""
    survey = get_object_or_404(Survey, pk=pk, project__created_by=request.user)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, 'Survey deleted successfully.')
        return redirect('surveys:survey_list')
    return render(request, 'surveys/survey_confirm_delete.html', {'survey': survey})

@login_required
def survey_responses(request, pk):
    """View responses for a survey."""
    survey = get_object_or_404(Survey, pk=pk, project__created_by=request.user)
    responses = SurveyResponse.objects.filter(survey=survey)
    return render(request, 'surveys/survey_responses.html', {
        'survey': survey,
        'responses': responses
    })

@login_required
def question_create(request, survey_pk):
    """Create a new question for a survey."""
    survey = get_object_or_404(Survey, pk=survey_pk, project__created_by=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey
            question.save()
            messages.success(request, 'Question added successfully.')
            return redirect('surveys:survey_detail', pk=survey.pk)
    else:
        form = QuestionForm()
    
    return render(request, 'surveys/question_form.html', {'form': form, 'survey': survey})

@login_required
def question_edit(request, survey_pk, pk):
    """Edit a question."""
    survey = get_object_or_404(Survey, pk=survey_pk, project__created_by=request.user)
    question = get_object_or_404(Question, pk=pk, survey=survey)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('surveys:survey_detail', pk=survey.pk)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'surveys/question_form.html', {'form': form, 'survey': survey, 'question': question})

@login_required
def question_delete(request, survey_pk, pk):
    """Delete a question."""
    survey = get_object_or_404(Survey, pk=survey_pk, project__created_by=request.user)
    question = get_object_or_404(Question, pk=pk, survey=survey)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('surveys:survey_detail', pk=survey.pk)
    return render(request, 'surveys/question_confirm_delete.html', {'survey': survey, 'question': question})

# Template Views
@login_required
def template_list(request):
    """List all survey templates."""
    templates = SurveyTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    projects = Project.objects.filter(created_by=request.user)
    return render(request, 'surveys/template_list.html', {
        'templates': templates,
        'projects': projects
    })

@login_required
def template_create(request):
    """Create a new survey template."""
    if request.method == 'POST':
        form = SurveyTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Template created successfully.')
            return redirect('surveys:template_detail', pk=template.pk)
    else:
        form = SurveyTemplateForm()
    
    return render(request, 'surveys/template_form.html', {'form': form})

@login_required
def template_edit(request, pk):
    """Edit a survey template."""
    template = get_object_or_404(SurveyTemplate, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = SurveyTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated successfully.')
            return redirect('surveys:template_detail', pk=template.pk)
    else:
        form = SurveyTemplateForm(instance=template)
    
    return render(request, 'surveys/template_form.html', {'form': form, 'template': template})

@login_required
def template_detail(request, pk):
    """Show detailed view of a survey template."""
    template = get_object_or_404(SurveyTemplate, pk=pk, created_by=request.user)
    projects = Project.objects.filter(created_by=request.user)
    return render(request, 'surveys/template_detail.html', {
        'template': template,
        'projects': projects
    })

@login_required
def template_question_create(request, template_pk):
    """Create a new question for a template."""
    template = get_object_or_404(SurveyTemplate, pk=template_pk, created_by=request.user)
    if request.method == 'POST':
        form = TemplateQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.template = template
            question.save()
            messages.success(request, 'Question added successfully.')
            return redirect('surveys:template_detail', pk=template.pk)
    else:
        form = TemplateQuestionForm()
    
    return render(request, 'surveys/template_question_form.html', {'form': form, 'template': template})

@login_required
def template_question_edit(request, template_pk, pk):
    """Edit a template question."""
    template = get_object_or_404(SurveyTemplate, pk=template_pk, created_by=request.user)
    question = get_object_or_404(TemplateQuestion, pk=pk, template=template)
    if request.method == 'POST':
        form = TemplateQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('surveys:template_detail', pk=template.pk)
    else:
        form = TemplateQuestionForm(instance=question)
    
    return render(request, 'surveys/template_question_form.html', {'form': form, 'template': template, 'question': question})

@login_required
def template_question_delete(request, template_pk, pk):
    """Delete a template question."""
    template = get_object_or_404(SurveyTemplate, pk=template_pk, created_by=request.user)
    question = get_object_or_404(TemplateQuestion, pk=pk, template=template)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('surveys:template_detail', pk=template.pk)
    return render(request, 'surveys/template_question_confirm_delete.html', {'template': template, 'question': question})

@login_required
def create_survey_from_template(request, template_pk):
    """Create a new survey from a template."""
    template = get_object_or_404(SurveyTemplate, pk=template_pk, created_by=request.user)
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=request.POST.get('project'), created_by=request.user)
        
        # Create the survey
        survey = Survey.objects.create(
            project=project,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            created_by=request.user,
            start_date=timezone.now().date()
        )
        
        # Copy questions from template
        for template_question in template.template_questions.all():
            Question.objects.create(
                survey=survey,
                text=template_question.text,
                swot_category=template_question.swot_category,
                order=template_question.order,
                is_required=template_question.is_required
            )
        
        messages.success(request, 'Survey created from template successfully.')
        return redirect('surveys:survey_detail', pk=survey.pk)
    
    return redirect('surveys:template_detail', pk=template.pk) 


@login_required
def social_media_list(request, survey_pk):
    """List all social media sources for a survey."""
    survey = get_object_or_404(Survey, pk=survey_pk, project__created_by=request.user)
    social_sources = SocialMediaSource.objects.filter(survey=survey)
    form = SocialMediaSourceForm(survey=survey)
    return render(request, 'surveys/social_media_list.html', {
        'survey': survey,
        'social_sources': social_sources,
        'form': form
    })

@login_required
def social_media_create(request, survey_pk):
    """Create a new social media source."""
    survey = get_object_or_404(Survey, pk=survey_pk, project__created_by=request.user)
    if request.method == 'POST':
        form = SocialMediaSourceForm(request.POST, survey=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Social media source added successfully.')
            return redirect('surveys:social_media_list', survey_pk=survey.pk)
    else:
        form = SocialMediaSourceForm(survey=survey)
    return render(request, 'surveys/social_media_list.html', {
        'survey': survey,
        'social_sources': SocialMediaSource.objects.filter(survey=survey),
        'form': form
    })

@login_required
def social_media_edit(request, pk):
    """Edit a social media source."""
    source = get_object_or_404(SocialMediaSource, pk=pk)
    survey = source.survey
    if request.method == 'POST':
        form = SocialMediaSourceForm(request.POST, instance=source, survey=survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Social media source updated successfully.')
            return redirect('surveys:social_media_list', survey_pk=survey.pk)
    else:
        form = SocialMediaSourceForm(instance=source, survey=survey)
    return render(request, 'surveys/social_media_list.html', {
        'survey': survey,
        'social_sources': SocialMediaSource.objects.filter(survey=survey),
        'form': form
    })

@login_required
def social_media_delete(request, pk):
    """Delete a social media source."""
    source = get_object_or_404(SocialMediaSource, pk=pk)
    survey = source.survey
    if request.method == 'POST':
        source.delete()
        messages.success(request, 'Social media source deleted successfully.')
        return redirect('surveys:social_media_list', survey_pk=survey.pk)
    return render(request, 'surveys/social_media_list.html', {
        'survey': survey,
        'social_sources': SocialMediaSource.objects.filter(survey=survey),
        'form': SocialMediaSourceForm(survey=survey)
    })

@login_required
def start_survey(request, pk):
    """Start collecting data from social media sources for a survey."""
    survey = get_object_or_404(Survey, pk=pk)
    
    if request.method == 'POST':
        try:
            error_message = start_survey_collection(survey)
            if error_message:
                # Split error messages by newline and display each one
                for error in error_message.split('\n'):
                    messages.error(request, error)
            else:
                messages.success(request, 'Survey data collection started successfully.')
        except Exception as e:
            messages.error(request, f'Error starting survey: {str(e)}')
    
    return redirect('surveys:survey_detail', pk=pk)

@login_required
def source_edit(request, pk):
    """Edit a social media source."""
    source = get_object_or_404(SocialMediaSource, pk=pk, survey__project__created_by=request.user)
    
    if request.method == 'POST':
        form = SocialMediaSourceForm(request.POST, instance=source, survey=source.survey)
        if form.is_valid():
            form.save()
            messages.success(request, 'Social media source updated successfully.')
            return redirect('surveys:survey_detail', pk=source.survey.pk)
    else:
        form = SocialMediaSourceForm(instance=source, survey=source.survey)
    
    return render(request, 'surveys/source_form.html', {
        'form': form,
        'source': source,
        'survey': source.survey,
        'title': 'Edit Social Media Source'
    })

        