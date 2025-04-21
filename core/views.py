from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.http import FileResponse
import os
from .models import Project, Survey, SWOTCategory, Question, Response
from .forms import ProjectForm, QuestionForm
from .utils import import_responses_from_excel, get_swot_summary, generate_survey_template, get_survey_statistics, export_swot_analysis, import_volunteers_from_excel
import pandas as pd
from .nlp_tools import analyze_survey_responses
import logging

# Set up logging with more detailed configuration
logger = logging.getLogger('surveys')
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

@login_required
def dashboard(request):
    """Main dashboard view showing recent projects and surveys."""
    user_projects = Project.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    recent_surveys = Survey.objects.filter(project__created_by=request.user).order_by('-created_at')[:5]
    
    context = {
        'user_projects': user_projects,
        'recent_surveys': recent_surveys,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def project_list(request):
    """List all projects for the current user."""
    projects = Project.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'core/project_list.html', {'projects': projects})

@login_required
def project_detail(request, pk):
    """Show detailed view of a project."""
    project = get_object_or_404(Project, pk=pk, created_by=request.user)
    active_surveys_count = project.surveys.filter(status='active').count()
    total_responses = sum(survey.responses.count() for survey in project.surveys.all())
    
    context = {
        'project': project,
        'active_surveys_count': active_surveys_count,
        'total_responses': total_responses,
    }
    return render(request, 'core/project_detail.html', context)

@login_required
def project_create(request):
    """Create a new project."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, 'Project created successfully.')
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'core/project_form.html', {'form': form})

@login_required
def project_edit(request, pk):
    """Edit an existing project."""
    project = get_object_or_404(Project, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'core/project_form.html', {'form': form, 'project': project})

@login_required
def project_delete(request, pk):
    """Delete a project."""
    project = get_object_or_404(Project, pk=pk, created_by=request.user)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('core:project_list')
    return render(request, 'core/project_confirm_delete.html', {'project': project})

@login_required
def import_responses(request, survey_id):
    """Import survey responses from Excel file."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, 'Please select an Excel file to import.')
            return redirect('core:import_responses', survey_id=survey_id)
        
        try:
            success_count, error_count, errors = import_responses_from_excel(survey_id, excel_file)
            
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} responses.')
            if error_count > 0:
                messages.warning(request, f'Failed to import {error_count} responses. Check the errors below.')
            
            # Get SWOT summary
            swot_summary = get_swot_summary(survey_id)
            
            context = {
                'survey': survey,
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'swot_summary': swot_summary
            }
            return render(request, 'core/import_results.html', context)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error importing responses: {str(e)}')
    
    return render(request, 'core/import_responses.html', {'survey': survey})

@login_required
def swot_analysis(request, survey_id):
    """Display SWOT analysis for a survey."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    swot_summary = get_swot_summary(survey_id)
    statistics = get_survey_statistics(survey_id)
    
    if request.method == 'POST':
        output_format = request.POST.get('format', 'excel')
        try:
            output_file = export_swot_analysis(survey_id, output_format)
            response = FileResponse(open(output_file, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="swot_analysis_{survey_id}.{output_format}"'
            return response
        except Exception as e:
            messages.error(request, f'Error exporting analysis: {str(e)}')
    
    context = {
        'survey': survey,
        'swot_summary': swot_summary,
        'statistics': statistics
    }
    return render(request, 'core/swot_analysis.html', context)

@login_required
def download_template(request, survey_id):
    """Download Excel template for survey responses."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    
    # Generate the template file
    template_path = generate_survey_template(survey)
    
    # Return the file as a response
    response = FileResponse(open(template_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="survey_{survey.id}_template.xlsx"'
    return response

@login_required
def question_create(request, survey_id):
    """Create a new SWOT-aligned question for a survey."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey
            question.save()
            messages.success(request, 'Question created successfully.')
            return redirect('surveys:survey_detail', pk=survey_id)
    else:
        form = QuestionForm()
    
    return render(request, 'core/question_form.html', {
        'form': form,
        'survey': survey
    })

@login_required
def question_edit(request, survey_id, question_id):
    """Edit an existing SWOT-aligned question."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    question = get_object_or_404(Question, id=question_id, survey=survey)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('surveys:survey_detail', pk=survey_id)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'core/question_form.html', {
        'form': form,
        'survey': survey,
        'question': question
    })

@login_required
def export_responses(request, survey_id):
    """Export survey responses to Excel file."""
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    
    # Get all responses for the survey
    responses = Response.objects.filter(survey=survey).select_related('question')
    
    # Create a DataFrame with the responses
    data = []
    for response in responses:
        data.append({
            'Question ID': response.question.id,
            'Question Text': response.question.text,
            'SWOT Category': response.question.swot_category.name,
            'Response': response.text,
            'Sentiment': response.sentiment_label,
            'Date': response.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(data)
    
    # Create a temporary Excel file
    output_file = f'survey_{survey_id}_responses.xlsx'
    df.to_excel(output_file, index=False)
    
    # Return the file as a response
    response = FileResponse(open(output_file, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{output_file}"'
    return response

@login_required
def survey_detail(request, survey_id=None, pk=None):
    """Show detailed view of a survey."""
    # Handle both pk and survey_id parameters
    survey_id = survey_id or pk
    survey = get_object_or_404(Survey, id=survey_id, project__created_by=request.user)
    responses = Response.objects.filter(survey=survey).select_related('question')
    logging.info(f"Hello {responses}")
    # Get analytics including word map
    analytics = analyze_survey_responses(responses)
    
    context = {
        'survey': survey,
        'responses': responses,
        'analytics': analytics,
    }
    return render(request, 'core/survey_detail.html', context) 

@login_required
def manage_volunteers(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, 'Please select an Excel file to import.')
            return redirect('core:manage_volunteers')
        
        try:
            success_count, error_count, errors = import_volunteers_from_excel(excel_file)
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} responses.')
            if error_count > 0:
                messages.warning(request, f'Failed to import {error_count} responses. Check the errors below.')
            
            context = {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
            }
            return render(request, 'core/import_volunteers.html', context)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error importing responses: {str(e)}')
    
    return render(request, 'core/import_volunteers.html')
