import nltk
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, ne_chunk
import string
from gensim import corpora
from gensim.models import LsiModel
import re
from textblob import TextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import io
import base64
from collections import Counter

# Download required NLTK data
nltk.download('vader_lexicon')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('wordnet')

# Initialize NLP tools
stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()
vader_analyzer = SentimentIntensityAnalyzer()

def preprocess_text(text):
    """Preprocess text for analysis."""
    if not isinstance(text, str):
        return ""
    
    # Tokenize and convert to lowercase
    tokens = word_tokenize(text.lower())
    
    # Remove stop words and punctuation
    filtered_tokens = [
        token for token in tokens 
        if token not in stop and token not in exclude
    ]
    
    # Lemmatize
    lemmatized_tokens = [lemma.lemmatize(token) for token in filtered_tokens]
    
    return ' '.join(lemmatized_tokens)

def get_sentiment(text):
    """Get sentiment score using VADER and TextBlob."""
    if not text:
        return 0.0, 'neutral'
    
    # VADER sentiment
    vader_scores = vader_analyzer.polarity_scores(text)
    vader_score = vader_scores['compound']
    
    # TextBlob sentiment
    blob = TextBlob(text)
    textblob_score = blob.sentiment.polarity
    
    # Combine scores (weighted average)
    combined_score = (0.6 * vader_score + 0.4 * textblob_score)
    
    # Determine label
    if combined_score < -0.2:
        label = 'negative'
    elif combined_score > 0.2:
        label = 'positive'
    else:
        label = 'neutral'
    
    return combined_score, label

def extract_topics(texts, num_topics=3, num_words=5):
    """Extract main topics from a collection of texts."""
    if not texts:
        return []
    
    # Preprocess texts
    processed_texts = [preprocess_text(text) for text in texts]
    
    # Create dictionary and corpus
    texts = [text.split() for text in processed_texts]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # Create LSI model
    lsi_model = LsiModel(corpus, num_topics=num_topics, id2word=dictionary)
    
    # Extract topics
    topics = []
    for topic in lsi_model.print_topics(num_topics=num_topics, num_words=num_words):
        words = [word.strip('"') for word in re.findall(r'"(.*?)"', topic[1])]
        topics.append(words)
    print(topics)
    return topics

def extract_named_entities(text):
    """Extract named entities from text."""
    if not text:
        return []
    
    # Tokenize and tag
    tokens = word_tokenize(text)
    pos_tags = pos_tag(tokens)
    named_entities = ne_chunk(pos_tags)
    
    # Extract entities
    entities = []
    for subtree in named_entities:
        if hasattr(subtree, 'label'):
            entity_name = " ".join(word for word, tag in subtree.leaves())
            entity_type = subtree.label()
            entities.append({
                'name': entity_name,
                'type': entity_type
            })
    
    return entities

def generate_word_map(texts, width=800, height=400):
    """Generate a word cloud image from the given texts."""
    if not texts:
        return None
    
    # Preprocess all texts
    processed_texts = [preprocess_text(text) for text in texts]
    
    # Combine all words and their frequencies
    all_words = ' '.join(processed_texts)
    
    # Create and generate word cloud
    wordcloud = WordCloud(
        width=width,
        height=height,
        background_color='white',
        max_words=100,
        min_font_size=10
    ).generate(all_words)
    
    # Convert plot to base64 string
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Save plot to bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    return graphic

def analyze_survey_responses(responses):
    """Analyze all responses for a survey and generate visualizations."""
    # Get all response texts
    texts = [r.text for r in responses if r.text]
    
    # Generate word map
    word_map = generate_word_map(texts)
    
    # Extract topics
    topics = extract_topics(texts)
    
    # Get sentiment distribution
    sentiments = [r.sentiment_label for r in responses]
    sentiment_counts = Counter(sentiments)
    
    # Collect all named entities
    all_entities = []
    for r in responses:
        entities = extract_named_entities(r.text)
        all_entities.extend(entities)
    
    # Count entities
    entity_counts = Counter([e['name'] for e in all_entities])
    
    return {
        'word_map': word_map,
        'topics': topics,
        'sentiment_counts': dict(sentiment_counts),
        'top_entities': dict(entity_counts.most_common(10))
    }

def analyze_text(text):
    """Perform comprehensive text analysis."""
    if not text:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'entities': []
        }
    
    # Preprocess text
    processed_text = preprocess_text(text)
    
    # Get sentiment
    sentiment_score, sentiment_label = get_sentiment(text)
    
    # Extract named entities
    entities = extract_named_entities(text)
    
    return {
        'sentiment_score': sentiment_score,
        'sentiment_label': sentiment_label,
        'entities': entities
    } 