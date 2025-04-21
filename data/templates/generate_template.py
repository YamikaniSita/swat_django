import pandas as pd
import os
import openpyxl

def create_survey_template():
    # Create a sample template with SWOT-aligned questions
    template_data = {
        'Question ID': [],
        'Question Text': [],
        'SWOT Category': [],
        'Response': [],
        'Notes': []
    }
    
    # Sample SWOT-aligned questions
    questions = [
        # Strengths
        ('Q1', 'What are the main strengths of the organization?', 'Strengths'),
        ('Q2', 'What unique capabilities does the organization have?', 'Strengths'),
        
        # Weaknesses
        ('Q3', 'What are the main areas for improvement?', 'Weaknesses'),
        ('Q4', 'What resources are lacking?', 'Weaknesses'),
        
        # Opportunities
        ('Q5', 'What market opportunities exist?', 'Opportunities'),
        ('Q6', 'What new technologies could be leveraged?', 'Opportunities'),
        
        # Threats
        ('Q7', 'What are the main competitive threats?', 'Threats'),
        ('Q8', 'What external factors could impact the organization?', 'Threats'),
    ]
    
    # Add questions to template
    for q_id, q_text, swot in questions:
        template_data['Question ID'].append(q_id)
        template_data['Question Text'].append(q_text)
        template_data['SWOT Category'].append(swot)
        template_data['Response'].append('')  # Empty for template
        template_data['Notes'].append('')     # Empty for template
    
    # Create DataFrame
    df = pd.DataFrame(template_data)
    
    # Create Excel writer
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, 'survey_responses_template.xlsx')
    
    # Write to Excel with formatting
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Responses')
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Responses']
        
        # Format column widths
        worksheet.column_dimensions['A'].width = 15  # Question ID
        worksheet.column_dimensions['B'].width = 50  # Question Text
        worksheet.column_dimensions['C'].width = 20  # SWOT Category
        worksheet.column_dimensions['D'].width = 40  # Response
        worksheet.column_dimensions['E'].width = 30  # Notes
        
        # Add header formatting
        for cell in worksheet[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
            cell.alignment = openpyxl.styles.Alignment(horizontal='center', vertical='center')
            cell.border = openpyxl.styles.Border(
                left=openpyxl.styles.Side(style='thin'),
                right=openpyxl.styles.Side(style='thin'),
                top=openpyxl.styles.Side(style='thin'),
                bottom=openpyxl.styles.Side(style='thin')
            )

if __name__ == '__main__':
    create_survey_template()
    print("Survey response template has been created successfully!") 