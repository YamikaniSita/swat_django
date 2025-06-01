import base64
from io import BytesIO
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from collections import Counter
import spacy
from gensim import corpora, models
from gensim.models import LsiModel
import numpy as np
from textblob import TextBlob
import re
from spacy.matcher import PhraseMatcher
from .models import Question, Response, SocialMediaResponse
from surveys.models import SocialMediaSource
import string
# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('vader_lexicon')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')
    nltk.download('wordnet')

# Initialize VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

known_political_entities = [
    "Democratic Progressive Party",
    "Malawi Congress Party",
    "United Transformation Movement",
    "President Lazarus Chakwera",
    "Vice President Saulos Chilima",
    "Ministry of Health",
    "Ministry of Education",
    "Blantyre District Council",
    "Mzuzu City Assembly",
    "National Registration Bureau",
    "Electoral Commission",
    "Parliament of Malawi",
    "Tonse Alliance",
    "DPP",
    "MCP",
    "UTM"
]


# Initialize spaCy for named entity recognition
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Downloading spaCy model...")
    import os
    os.system('python -m spacy download en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

def preprocess_text(text):
    """Preprocess text for analysis."""
    # Tokenize
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    return ' '.join(tokens)

def get_sentiment(text):
    """Get sentiment analysis for text."""
    vader = SentimentIntensityAnalyzer()
    blob_score = TextBlob(text).sentiment.polarity
    vader_score = vader.polarity_scores(text)['compound']
    
    # Combine with simple average
    final_score = (blob_score + vader_score) / 2
    
    if final_score >= 0.05:
        return 'positive'
    elif final_score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

def extract_topics(texts, num_topics=5):
    """Extract main topics from texts using LDA."""
    # Preprocess texts
    processed_texts = [preprocess_text(text) for text in texts]
    
    # Create dictionary and corpus
    dictionary = corpora.Dictionary([text.split() for text in processed_texts])
    corpus = [dictionary.doc2bow(text.split()) for text in processed_texts]
    
    # Train LDA model
    lda_model = models.LdaModel(corpus=corpus, num_topics=num_topics, id2word=dictionary, passes=15)
    
    # Get topics
    topics = []
    for topic_id in range(num_topics):
        topic = lda_model.show_topic(topic_id, topn=5)
        topics.append([word for word, _ in topic])
    
    return topics

def custom_entities(text, known_entities):
    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp.make_doc(ent) for ent in known_entities]
    matcher.add("CUSTOM_ENTITIES", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for match_id, start, end in matches]))

def extract_named_entities(text):
    """Extract named entities from text."""
    doc = nlp(text)
    entities = [ent.text for ent in doc.ents]
    return entities

def generate_word_map(texts):
    """Generate word cloud from texts."""
    # Combine all texts
    combined_text = ' '.join(texts)
    
    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(combined_text)
    
    # Convert to base64
    img = BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def analyze_text(text):
    """
    Analyze a single text input and return sentiment, topics, and entities.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing sentiment, topics, and entities
    """
    # Clean text
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#', '', text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    
    # Get sentiment using VADER
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(text)
    
    # Determine sentiment
    if sentiment_scores['compound'] >= 0.05:
        sentiment = 'positive'
    elif sentiment_scores['compound'] <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    # Get topics using TextBlob
    blob = TextBlob(text)
    topics = []
    for word, tag in blob.tags:
        if tag.startswith('NN'):  # Nouns
            topics.append(word.lower())
    
    # Get entities using spaCy
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities = [ent.text for ent in nlp(text).ents if ent.label_ in ['ORG', 'GPE', 'PERSON']]
        entities += custom_entities(text, known_political_entities)

    
    return {
        'sentiment': sentiment,
        'topics': list(set(topics))[:5],  # Top 5 unique topics
        'entities': list(set(entities))[:5],  # Top 5 unique entities
        'sentiment_scores': sentiment_scores
    }



def analyze_survey_responses(responses, word_map=False):
    """
    Analyze all responses for a survey and generate analytics.
    
    Args:
        responses (QuerySet): QuerySet of Response objects
        
    Returns:
        dict: Dictionary containing analytics results
    """
    if not responses:
        return None

    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    all_entities = []
    text_for_topics = []
    text_for_word_map = []

    for response in responses:
        if not response.text:
            continue
        try:
            data_required = getattr(response.question, 'required_data')
            print(data_required)
        except:
            data_required = getattr(response.social_source, 'required_data')
        print(data_required)

        if data_required in ['all', 'sentiment']:
            analysis = analyze_text(response.text)
            sentiment_counts[analysis['sentiment']] += 1
        
        if data_required in ['all', 'topics']:
            analysis = analyze_text(response.text)
            all_entities.extend(analysis['entities'])
            text_for_topics.append(response.text)
            text_for_word_map.append(response.text)
        

    # Generate word map
    if word_map:
        word_map = generate_word_map(text_for_word_map)

    # Top NER entities
    top_entities = dict(Counter(all_entities).most_common(10))

    # Topic modeling
    stop_words = stopwords.words('english')
    topics = extract_topics(text_for_topics, num_topics=5) if text_for_topics else []
    main_topics = extract_top_keywords(topics, top_n=10)
    main_topics = [word for word in main_topics if word not in stop_words]

    return {
        'sentiment_counts': sentiment_counts,
        'top_entities': top_entities,
        'topics': main_topics,
        'total_responses': len(responses),
        'word_map': word_map
    }


def extract_top_keywords(topics, top_n=10):
    """
    Given a list of topic word lists, return the top N most frequent keywords.
    """
    all_keywords = [word for topic in topics for word in topic]
    keyword_counts = Counter(all_keywords)
    return dict(keyword_counts.most_common(top_n))


def generate_survey_report(survey):
    """
    Generate a comprehensive report for a given survey.
    
    Args:
        survey (Survey): The survey object to analyze
        
    Returns:
        dict: Dictionary containing the report
    """
    report_dict = {} 
    question_responses = Question.objects.filter(survey=survey)
    for question in question_responses:
        responses = Response.objects.filter(question=question)
        if responses.exists():
            data_required = getattr(question, 'required_data', 'all')
            sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
            all_entities = []
            text_for_topics = []
            for response in responses:
                if data_required in ['all', 'sentiment']:
                    analysis = analyze_text(response.text)
                    sentiment_counts[analysis['sentiment']] += 1

                if data_required in ['all', 'topics']:
                    analysis = analyze_text(response.text)
                    all_entities.extend(analysis['entities'])
                    text_for_topics.append(response.text)
            top_entities = dict(Counter(all_entities).most_common(10))
            # Topic modeling
            stop_words = stopwords.words('english')
            topics = extract_topics(text_for_topics, num_topics=5) if text_for_topics else []
            main_topics = extract_top_keywords(topics, top_n=10)
            main_topics = [word for word in main_topics if word not in stop_words]
            report_dict[question.text] = {'required_data': question.required_data, 'swot_category': question.swot_category.name, 'sentiment_counts': sentiment_counts, 'top_entities': top_entities, 'top_topics': main_topics}
        else:
            report_dict[question.text] = None
    
    # for social media responses
    social_sources_report = {}
    for social_sources in SocialMediaSource.objects.filter(survey=survey):
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        all_entities = []
        text_for_topics = []
        data_required = getattr(social_sources, 'required_data', 'all')
        print(data_required)
        for social_response in SocialMediaResponse.objects.filter(survey=survey, social_source=social_sources):
            print(social_response.text)
            if not social_response.text:
                continue
            if data_required in ['all', 'sentiment']:
                analysis = analyze_text(social_response.text)
                sentiment_counts[analysis['sentiment']] += 1

            if data_required in ['all', 'topics']:
                analysis = analyze_text(social_response.text)
                all_entities.extend(analysis['entities'])
                text_for_topics.append(social_response.text)
        top_entities = dict(Counter(all_entities).most_common(10))
        # Topic modeling
        stop_words = stopwords.words('english')
        topics = extract_topics(text_for_topics, num_topics=5) if text_for_topics else []
        main_topics = extract_top_keywords(topics, top_n=10)
        main_topics = [word for word in main_topics if word not in stop_words]
        social_sources_report[social_sources.source_name] = {'platform': social_sources.platform,'required_data': social_sources.required_data, 'sentiment_counts': sentiment_counts, 'top_entities': top_entities, 'top_topics': main_topics}
    print(social_sources_report)
    return [report_dict, social_sources_report]

