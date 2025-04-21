from itertools import accumulate
import pandas as pd
import os
import openpyxl
from django.core.exceptions import ValidationError
from .models import Location, Survey, Question, Response, SWOTCategory, Volunteers
from django.db import models
from django.utils import timezone
from .nlp_tools import analyze_text


def import_responses_from_excel(survey_id, excel_file):
    """
    Import survey responses from an Excel file.
    
    Args:
        survey_id (int): The ID of the survey to import responses for
        excel_file: The uploaded Excel file
    
    Returns:
        tuple: (success_count, error_count, errors)
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Validate required columns
        required_columns = ['Question ID', 'Response']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Get the survey
        survey = Survey.objects.get(id=survey_id)
        
        # Create a mapping of question IDs to Question objects
        questions = {q.id: q for q in survey.questions.all()}
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                question_id = row['Question ID']
                response_text = str(row['Response']).strip()
                
                if not response_text:
                    continue
                
                if question_id not in questions:
                    error_count += 1
                    errors.append(f"Row {index + 2}: Question ID '{question_id}' not found")
                    continue
                
                # Perform NLP analysis
                analysis = analyze_text(response_text)
                
                # Create the response with NLP results
                Response.objects.create(
                    survey=survey,
                    question=questions[question_id],
                    text=response_text,
                    sentiment_score=analysis['sentiment_score'],
                    sentiment_label=analysis['sentiment_label']
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return success_count, error_count, errors
        
    except Exception as e:
        raise ValidationError(f"Error processing Excel file: {str(e)}")

def get_swot_summary(survey_id):
    """
    Get a summary of responses grouped by SWOT category.
    
    Args:
        survey_id (int): The ID of the survey
    
    Returns:
        dict: Summary of responses by SWOT category
    """
    survey = Survey.objects.get(id=survey_id)
    
    summary = {
        'strengths': [],
        'weaknesses': [],
        'opportunities': [],
        'threats': []
    }
    
    # Get all responses for the survey
    responses = Response.objects.filter(survey=survey).select_related('question', 'question__swot_category')
    
    for response in responses:
        category_name = response.question.swot_category.name.lower()
        if category_name in summary:
            summary[category_name].append({
                'question': response.question.text,
                'response': response.text,
                'sentiment': response.sentiment_label
            })
    
    return summary

def generate_survey_template(survey):
    """
    Generate an Excel template for survey responses.
    
    Args:
        survey: The Survey object
    
    Returns:
        str: Path to the generated template file
    """
    # Create a DataFrame with the questions
    data = []
    for question in survey.questions.all():
        data.append({
            'Question ID': question.id,
            'Question Text': question.text,
            'SWOT Category': question.swot_category.name,
            'Response': '',  # Empty column for responses
            'Notes': ''      # Optional notes column
        })
    
    df = pd.DataFrame(data)
    
    # Create a temporary Excel file
    output_file = f'survey_{survey.id}_template.xlsx'
    df.to_excel(output_file, index=False)
    
    return output_file

def get_survey_statistics(survey_id):
    """
    Get detailed statistics for a survey.
    
    Args:
        survey_id (int): The ID of the survey
    
    Returns:
        dict: Survey statistics
    """
    survey = Survey.objects.get(id=survey_id)
    
    # Get all responses
    responses = Response.objects.filter(survey=survey)
    
    # Calculate basic statistics
    total_responses = responses.count()
    questions_count = survey.questions.count()
    
    # Calculate responses per SWOT category
    category_counts = {}
    for category in SWOTCategory.objects.all():
        count = responses.filter(question__swot_category=category).count()
        category_counts[category.name.lower()] = count
    
    # Calculate sentiment distribution
    sentiment_counts = {
        'positive': responses.filter(sentiment_label='positive').count(),
        'neutral': responses.filter(sentiment_label='neutral').count(),
        'negative': responses.filter(sentiment_label='negative').count(),
    }
    
    # Calculate average sentiment score
    avg_sentiment = responses.exclude(sentiment_score__isnull=True).aggregate(
        avg_score=models.Avg('sentiment_score')
    )['avg_score'] or 0
    
    return {
        'total_responses': total_responses,
        'questions_count': questions_count,
        'category_counts': category_counts,
        'sentiment_counts': sentiment_counts,
        'avg_sentiment': round(avg_sentiment, 2),
        'response_rate': round((total_responses / questions_count) * 100, 1) if questions_count > 0 else 0
    }

def export_swot_analysis(survey_id, output_format='excel'):
    """
    Export SWOT analysis results.
    
    Args:
        survey_id (int): The ID of the survey
        output_format (str): 'excel' or 'csv'
    
    Returns:
        str: Path to the exported file
    """
    survey = Survey.objects.get(id=survey_id)
    swot_summary = get_swot_summary(survey_id)
    statistics = get_survey_statistics(survey_id)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join('data', 'exports')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create output file path
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    if output_format == 'excel':
        output_file = os.path.join(output_dir, f'swot_analysis_{survey.id}_{timestamp}.xlsx')
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write SWOT Summary
            for category in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                data = []
                for item in swot_summary[category]:
                    data.append({
                        'Question': item['question'],
                        'Response': item['response'],
                        'Sentiment': item.get('sentiment', '')
                    })
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=category.title(), index=False)
            
            # Write Statistics
            stats_data = {
                'Metric': [
                    'Total Responses',
                    'Questions Count',
                    'Response Rate (%)',
                    'Average Sentiment Score',
                    'Positive Responses',
                    'Neutral Responses',
                    'Negative Responses'
                ],
                'Value': [
                    statistics['total_responses'],
                    statistics['questions_count'],
                    statistics['response_rate'],
                    statistics['avg_sentiment'],
                    statistics['sentiment_counts']['positive'],
                    statistics['sentiment_counts']['neutral'],
                    statistics['sentiment_counts']['negative']
                ]
            }
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='Statistics', index=False)
            
            # Write Category Distribution
            df_categories = pd.DataFrame({
                'Category': list(statistics['category_counts'].keys()),
                'Count': list(statistics['category_counts'].values())
            })
            df_categories.to_excel(writer, sheet_name='Category Distribution', index=False)
            
    else:  # CSV format
        output_file = os.path.join(output_dir, f'swot_analysis_{survey.id}_{timestamp}.csv')
        # Combine all data into a single DataFrame
        all_data = []
        for category in ['strengths', 'weaknesses', 'opportunities', 'threats']:
            for item in swot_summary[category]:
                all_data.append({
                    'Category': category.title(),
                    'Question': item['question'],
                    'Response': item['response'],
                    'Sentiment': item.get('sentiment', '')
                })
        df = pd.DataFrame(all_data)
        df.to_csv(output_file, index=False)
    
    return output_file 

def import_volunteers_from_excel(excel_file):
    """
    Import survey responses from an Excel file.
    
    Args:
        survey_id (int): The ID of the survey to import responses for
        excel_file: The uploaded Excel file
    
    Returns:
        tuple: (success_count, error_count, errors)
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        # Validate required columns
        required_columns = ['Name', 'Phone Number', 'Region']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Get the survey
        
        # Create a mapping of question IDs to Question objects
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                name = str(row['Name']).strip()
                phone_number = str(row['Phone Number']).strip()
                region = str(row['Region']).strip()
                
                if not name or not phone_number or not region:
                    continue
            
               
                regions = region.split("|")
               

                # National level
                nation, _ = Location.objects.get_or_create(
                    name = regions[0],
                    defaults={'location_type':"National"}
                )

                #Regional
                region_, _ = Location.objects.get_or_create(
                    name = regions[1],
                    defaults={'location_type':"Regional", "parent": nation}
                )

                #District
                district, _ = Location.objects.get_or_create(
                    name = regions[2],
                    defaults={'location_type':"District", "parent": region_}
                )


                #Constituenct
                constituency, _ = Location.objects.get_or_create(
                    name = regions[3],
                    defaults={'location_type':"Constituency", "parent": district}
                )

                Volunteers.objects.create(
                    name = name,
                    phone_number = phone_number,
                    region = region,
                    location_id = constituency
                )
                success_count += 1

                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index + 2}: {str(e)}")
        print(errors)
        return success_count, error_count, errors
        
    except Exception as e:
        raise ValidationError(f"Error processing Excel file: {str(e)}")
    



