from itertools import accumulate
import string
import pandas as pd
import os
import openpyxl
from django.core.exceptions import ValidationError
import requests

from surveys.models import SocialMediaSource
from .models import Location, SocialMediaResponse, Survey, Question, Response, SWOTCategory, Volunteers
from django.db import models
from django.utils import timezone
from .nlp_tools import analyze_text
from langdetect import detect_langs
import urllib
from django.db.models import Q


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
        required_columns = ['Question ID', 'Response', 'Volunteer Phone Number']
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
                volunteer_phone_number = str(row['Volunteer Phone Number'])
                
                if not response_text:
                    continue
                
                if question_id not in questions:
                    error_count += 1
                    errors.append(f"Row {index + 2}: Question ID '{question_id}' not found")
                    continue
                translated_from = ""
                detected_language = detect_langs(response_text)
                if detected_language[0].lang != 'en' or detected_language[0].prob < 0.9:
                    print(f"== Language detected {detected_language[0].lang} at probability {detected_language[0].prob} attempting translation")
                    params = {'client': 'dict-chrome-ex', 'sl': 'ny', 'tl': 'en', 'q': response_text}
                    params_encoded = urllib.parse.urlencode(params)
                    # print("https://clients5.google.com/translate_a/t?"+params_encoded)
                    request_result = requests.get("https://clients5.google.com/translate_a/t?"+params_encoded).json()
                    translated_from = response_text
                    response_text = request_result[0]
                    # Perform NLP analysis
                    response_text = response_text.translate(str.maketrans('', '', string.punctuation))
                    print(response_text)
                    analysis = analyze_text(response_text)
                else:
                    response_text = response_text.translate(str.maketrans('', '', string.punctuation))
                    print(response_text)
                    analysis = analyze_text(response_text)
                volunteer = Volunteers.objects.filter(phone_number = volunteer_phone_number).first()
                
                # Create the response with NLP results
                a = Response.objects.get_or_create(
                    survey=survey,
                    question=questions[question_id],
                    text=response_text,
                    volunteer = volunteer,
                    sentiment_score=analysis['sentiment_score'],
                    sentiment_label=analysis['sentiment_label'],
                    translated_from = translated_from
                )
                # print(a)
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
    responses = Response.objects.filter(survey=survey, question__required_data__in=["all", "sentiment"]).select_related('question', 'question__swot_category')
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
            'Volunteer Phone Number': "",
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

    social_media_sources = SocialMediaSource.objects.filter(survey=survey).count()
    social_media_responses = SocialMediaResponse.objects.filter(survey=survey).count()
    print(social_media_responses, social_media_sources)

    
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
        'positive': responses.filter(sentiment_label='positive',  question__required_data__in=["all", "sentiment"]).count(),
        'neutral': responses.filter(sentiment_label='neutral',  question__required_data__in=["all", "sentiment"]).count(),
        'negative': responses.filter(sentiment_label='negative',  question__required_data__in=["all", "sentiment"]).count(),
    }
   
    avg_sentiment = responses.filter(question__required_data = "topics").values('sentiment_score', 'question__required_data').aggregate(
            avg_score=models.Avg('sentiment_score')
        )['avg_score'] or 0
    
    return {
        'total_responses': total_responses,
        'questions_count': questions_count,
        'category_counts': category_counts,
        'sentiment_counts': sentiment_counts,
        'avg_sentiment': round(avg_sentiment, 2),
        'response_rate': round((total_responses / questions_count) * 100, 1) if questions_count > 0 else 0,
        'setup_social_sources': social_media_sources,
        'indexed_social_responses': social_media_responses
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
    from django.utils.dateparse import parse_date
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        # Validate required columns
        required_columns = ['Name', 'Phone Number', 'Region', 'Sex', 'Birthdate']
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
                sex = str(row['Sex']).strip()
                birthdate = parse_date(str(row['Birthdate']).strip().split()[0])
                
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
                    birthdate = birthdate,
                    sex = sex,
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
    
def build_recommendation_prompt(full_report):
    lines = ["Below is a summary report from a survey (SMS qestionnaire-SWOT assessment all open ended questions, we also obtained some social media comments from related posts on the candidates pages in the reported they are tagged as 'Social Media Analysis') conducted for a candidate running for MP in a rural area, we conducted NLP analysis:\n"]
    count = 1

    for section in full_report:
        for question, details in section.items():
            lines.append(f"{count}. Question: {question}")
            lines.append(f"   - SWOT Category: {details.get('swot_category', 'N/A')}")
            sc = details.get("sentiment_counts", {})
            lines.append(f"   - Sentiment: {sc.get('positive', 0)} positive, {sc.get('neutral', 0)} neutral, {sc.get('negative', 0)} negative")
            topics = ", ".join(details.get("top_topics", []))
            lines.append(f"   - Topics: {topics or 'None'}")
            entities = ", ".join(details.get("top_entities", {}).keys())
            lines.append(f"   - Entities: {entities or 'None'}\n")
            count += 1

    lines.append("Based on this report, suggest actions in a paragraph the candidate should consider doing to achieve their goal.")
    return "\n".join(lines)


def get_ai_recommendations(full_report):
    from groq import Groq
    """
    Get AI recommendations based on the SWOT analysis report.
    
    Args:
        full_report (dict): The SWOT analysis report
    
    Returns:
        str: AI-generated recommendations
    """
    try:
        prompt = build_recommendation_prompt(full_report)
        api_key=os.getenv("GROQ_API_KEY")
        print(f"Using Groq API key: {api_key}")
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            # The language model which will generate the completion.
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        )
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"Error generating AI recommendations: {str(e)}")
        return "AI Recommendations are not available at the moment. Please try again later."
    



