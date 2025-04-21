# Political Sentiment System

A Django-based system for tracking political sentiment through SWOT surveys and social media monitoring.

## Features

- Project Management
- Volunteer Management
- SMS-Based SWOT Surveys
- Social Media Sentiment Analysis
- Analytical Insights and Reporting

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost:3306/dbname
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

- `projects/` - Main project configuration
- `core/` - Core functionality and models
- `surveys/` - Survey management
- `volunteers/` - Volunteer management
- `analytics/` - Sentiment analysis and reporting
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)

## Usage

1. Log in to the admin interface
2. Create a new project
3. Add volunteers
4. Create and administer surveys
5. View analytics and reports

## Development

- Python 3.8+
- Django 4.2+
- MySQL 8.0+ 