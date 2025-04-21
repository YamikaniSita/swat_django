from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SentimentAnalysis, TopicAnalysis, NamedEntity, ProjectReport
from core.models import Project, Survey

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard."""
    recent_analyses = SentimentAnalysis.objects.all().order_by('-analyzed_at')[:5]
    recent_topics = TopicAnalysis.objects.all().order_by('-analyzed_at')[:5]
    recent_entities = NamedEntity.objects.all().order_by('-extracted_at')[:5]
    
    context = {
        'recent_analyses': recent_analyses,
        'recent_topics': recent_topics,
        'recent_entities': recent_entities,
    }
    return render(request, 'analytics/dashboard.html', context)

@login_required
def sentiment_analysis(request):
    """View sentiment analysis results."""
    analyses = SentimentAnalysis.objects.all().order_by('-analyzed_at')
    return render(request, 'analytics/sentiment_analysis.html', {'analyses': analyses})

@login_required
def topic_analysis(request):
    """View topic analysis results."""
    topics = TopicAnalysis.objects.all().order_by('-analyzed_at')
    return render(request, 'analytics/topic_analysis.html', {'topics': topics})

@login_required
def named_entity_analysis(request):
    """View named entity analysis results."""
    entities = NamedEntity.objects.all().order_by('-extracted_at')
    return render(request, 'analytics/named_entity_analysis.html', {'entities': entities})

@login_required
def report_list(request):
    """List all reports."""
    reports = ProjectReport.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'analytics/report_list.html', {'reports': reports})

@login_required
def report_create(request):
    """Create a new report."""
    if request.method == 'POST':
        # Form handling will be added later
        pass
    return render(request, 'analytics/report_form.html')

@login_required
def report_detail(request, pk):
    """Show detailed view of a report."""
    report = get_object_or_404(ProjectReport, pk=pk, created_by=request.user)
    return render(request, 'analytics/report_detail.html', {'report': report})

@login_required
def report_download(request, pk):
    """Download a report."""
    report = get_object_or_404(ProjectReport, pk=pk, created_by=request.user)
    # Report download functionality will be added later
    return redirect('analytics:report_detail', pk=pk) 