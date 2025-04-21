from itertools import islice
import os
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import SocialMediaSource
from core.models import Location, Question, Response, SocialMediaResponse, Volunteers
from core.analytics import analyze_text
import logging
import json
from langdetect import detect, detect_langs
import urllib

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

class FacebookService:
    def __init__(self, source=None):
        self.source = source
        self.token = None
        self.api_version = 'v22.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
        # Try to get token from source first
        if source and source.platform == 'facebook' and source.access_token:
            self.token = source.access_token
            logger.info(f"Using source-specific token for {source.source_name}")
        else:
            # Fall back to environment token
            self.token = os.getenv('FB_TOKEN')
            if not self.token:
                logger.error("No valid Facebook token found (neither source-specific nor environment)")
                raise ValueError("No valid Facebook token found")
            logger.info("Using environment token")
        
        # Log token info (first few characters only for security)
        logger.info(f"Using token starting with: {self.token[:10]}...")

    def validate_token(self):
        """Validate the access token by making a simple API call."""
        if not self.token:
            logger.error("No token available for validation")
            return False, "No token available"
            
        endpoint = f'{self.base_url}/me'
        params = {
            'access_token': self.token,
            'fields': 'id,name'
        }
        
        # Log request details (masking token)
        masked_params = params.copy()
        masked_params['access_token'] = f"{self.token[:10]}..."
        logger.info(f"Validating token - Request URL: {endpoint}")
        logger.info(f"Request params: {json.dumps(masked_params, indent=2)}")
        
        try:
            response = requests.get(endpoint, params=params)
            logger.info(f"Token validation response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Token validation successful for user: {data.get('name')}")
                return True, None
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Token validation failed: {response.status_code}")
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                return False, error_message
        except Exception as e:
            error_message = f"Token validation error: {str(e)}"
            logger.error(error_message)
            return False, error_message

    def get_page_posts(self, page_id, until_date=None):
        """Fetch posts from a Facebook page."""
        if not self.token:
            logger.error("No token available for fetching posts")
            return []
            
        endpoint = f'{self.base_url}/{page_id}/posts'
        params = {
            'access_token': self.token,
            'fields': 'id,message,created_time,comments.summary(true),reactions.summary(true)',
            'limit': 100
        }
        
        if until_date:
            params['until'] = until_date.strftime('%Y-%m-%d')
            
        # Log request details (masking token)
        masked_params = params.copy()
        masked_params['access_token'] = f"{self.token[:10]}..."
        logger.info(f"Fetching posts for page {page_id}")
        logger.info(f"Request URL: {endpoint}")
        logger.info(f"Request params: {json.dumps(masked_params, indent=2)}")
        
        try:
            response = requests.get(endpoint, params=params)
            logger.info(f"Posts fetch response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', [])
                logger.info(f"Successfully fetched {len(posts)} posts")
                
                # Log first post details as sample
                if posts:
                    first_post = posts[0]
                    logger.info("Sample post data:")
                    logger.info(f"Post ID: {first_post.get('id')}")
                    logger.info(f"Created time: {first_post.get('created_time')}")
                    logger.info(f"Message length: {len(first_post.get('message', ''))} characters")
                    logger.info(f"Comments count: {first_post.get('comments', {}).get('summary', {}).get('total_count', 0)}")
                    logger.info(f"Reactions count: {first_post.get('reactions', {}).get('summary', {}).get('total_count', 0)}")
                
                return posts
            else:
                error_data = response.json()
                logger.error(f"Failed to fetch posts: {response.status_code}")
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                return []
        except Exception as e:
            logger.error(f"Error fetching posts: {str(e)}")
            return []

    def process_comments(self, post_id, survey):
        """Process comments for a Facebook post."""
        if not self.token:
            logger.error("No token available for fetching comments")
            print("ERROR: No token available for fetching comments")
            return []
        
        endpoint = f'{self.base_url}/{post_id}/comments'
        params = {
            'access_token': self.token,
            'fields': 'id,message,created_time,from',
            'limit': 100
        }
        
        try:
            response = requests.get(endpoint, params=params)
            if response.status_code == 200:
                data = response.json()
                comments = data.get('data', [])
                logger.info(f"Successfully fetched {len(comments)} comments for post {post_id}")
                print(f"\n=== Fetched {len(comments)} comments for post {post_id} ===")
                
                # Log each comment's details
                for comment in comments:
                    logger.info("\n=== Comment Details ===")
                    logger.info(f"Comment ID: {comment.get('id')}")
                    logger.info(f"From: {comment.get('from', {}).get('name', 'Unknown')}")
                    logger.info(f"Created Time: {comment.get('created_time')}")
                    logger.info(f"Message: {comment.get('message', '')}")
                    logger.info("=== End Comment Details ===\n")
                    logger.info(f"--Language {detect_langs(comment.get('message', ''))}")
                    # Print the same information
                    print("\n=== Comment Details ===")
                    print(f"Comment ID: {comment.get('id')}")
                    print(f"From: {comment.get('from', {}).get('name', 'Unknown')}")
                    print(f"Created Time: {comment.get('created_time')}")
                    print(f"Message: {comment.get('message', '')}")
                    print("=== End Comment Details ===\n")
                
                return comments
            else:
                error_msg = f"Failed to fetch comments: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"Response: {response.text}")
                print(error_msg)
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            error_msg = f"Error fetching comments: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return []

    def process_posts(self, source, survey):
        """Process posts and create responses if they match topics."""
        logger.info(f"Processing posts for source: {source.source_name} (ID: {source.source_id})")
        source.total_pull_requests += 1
        
        # Validate token first
        is_valid, error_message = self.validate_token()
        if not is_valid:
            source.failed_pull_requests += 1
            source.last_error = error_message
            source.save()
            logger.error(f"Token validation failed: {error_message}")
            return error_message
        
        try:
            # Use survey end date as until_date
            posts = self.get_page_posts(source.source_id, until_date=survey.end_date)
            source.successful_pull_requests += 1
            source.last_error = None
            logger.info(f"Successfully fetched {len(posts)} posts")
        except Exception as e:
            source.failed_pull_requests += 1
            source.last_error = str(e)
            source.save()
            logger.error(f"Failed to process posts: {str(e)}")
            return str(e)

        topics = [topic.strip().lower() for topic in source.topics.split(',')]
        logger.info(f"Monitoring topics: {topics}")
        
        source.indexed_posts = len(posts)
        matching_count = 0
        
        for post in posts:
            if not post.get('message'):
                logger.debug(f"Skipping post {post.get('id')} - no message")
                continue

            # Check if post is within survey date range
            post_date = datetime.strptime(post['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
            
            # Convert survey end date to naive datetime for comparison
            if timezone.is_aware(survey.end_date):
                survey_end = timezone.make_naive(survey.end_date)
            else:
                survey_end = survey.end_date
            
            if post_date > survey_end:
                logger.debug(f"Skipping post {post.get('id')} - after survey end date")
                continue

            # Check if post contains any of the topics
            message = post['message'].lower()
            logger.info(f"\nChecking post: {post.get('id')}")
            logger.info(f"Message: {message}")
            
            matching_topics = [topic for topic in topics if topic in message]
            if matching_topics:
                logger.info(f"Found matching topics: {matching_topics}")
                matching_count += 1
            else:
                logger.info("No matching topics found")
                continue

            logger.info(f"Found matching post: {post.get('id')}")
            
            # Check if response already exists
            if SocialMediaResponse.objects.filter(survey=survey, source_id=post['id']).exists():
                logger.info(f"Response already exists for post {post.get('id')}, skipping")
                continue
                
            # Commented out as we no longer analyse posts just comments

            # Analyze the post content
            #check language
            translated_from = None
            detected_language = detect_langs(post['message'].lower())
            logger.info(f"Detected language{detected_language}")
            if detected_language[0].lang != 'en' or detected_language[0].prob < 0.9:
                logger.info(f"== Language detected {detected_language[0].lang} at probability {detected_language[0].prob} attempting translation")
                params = {'client': 'dict-chrome-ex', 'sl': 'ny', 'tl': 'en', 'q': message}
                params_encoded = urllib.parse.urlencode(params)
                # print("https://clients5.google.com/translate_a/t?"+params_encoded)
                request_result = requests.get("https://clients5.google.com/translate_a/t?"+params_encoded).json()
                logger.info(f"== Text received from google {request_result[0]}")
                translated_from = post['message']
                post['message'] = request_result[0]

            analysis = analyze_text(post['message'])
            logger.info(f"Analysis results: {analysis}")
            
            # Create a social media response
            response = SocialMediaResponse.objects.create(
                survey=survey,
                source_type='facebook',
                source_id=post['id'],
                text=post['message'],
                sentiment_score=analysis.get('sentiment_scores', {}).get('compound', 0.0),
                sentiment_label=analysis.get('sentiment', 'neutral'),
                topics=analysis.get('topics', []),
                entities=analysis.get('entities', []),
                translated_from = translated_from,
                created_at=post_date
            )
            logger.info(f"Created response with ID: {response.id}")

            # Process comments for this post
            comments = self.process_comments(post['id'], survey)
            for comment in comments:
                try:
                    comment_date = datetime.strptime(comment['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
                    if comment_date > survey_end:
                        continue
                        
                    # Check if comment response already exists
                    if SocialMediaResponse.objects.filter(survey=survey, source_id=comment['id']).exists():
                        continue
                        
                    # Analyze comment content
                    #check language
                    translated_from = None
                    detected_language = detect_langs(comment['message'].lower())
                    logger.info(f"Detected for comment language{detected_language}")
                    if detected_language[0].lang != 'en' or detected_language[0].prob < 0.9:
                        logger.info(f"== Language detected {detected_language[0].lang} at probability {detected_language[0].prob} attempting translation")
                        params = {'client': 'dict-chrome-ex', 'sl': 'ny', 'tl': 'en', 'q': comment['message']}
                        params_encoded = urllib.parse.urlencode(params)
                        request_result = requests.get("https://clients5.google.com/translate_a/t?"+params_encoded).json()
                        logger.info(f"== Text received from google {request_result[0]}")
                        translated_from = comment['message']
                        comment['message'] = request_result[0]
                        
                    
                    comment_analysis = analyze_text(comment['message'])
                    
                    # Create response for comment
                    SocialMediaResponse.objects.create(
                        survey=survey,
                        source_type='facebook_comment',
                        source_id=comment['id'],
                        text=comment['message'],
                        sentiment_score=comment_analysis.get('sentiment_scores', {}).get('compound', 0.0),
                        sentiment_label=comment_analysis.get('sentiment', 'neutral'),
                        topics=comment_analysis.get('topics', []),
                        entities=comment_analysis.get('entities', []),
                        translated_from=translated_from,
                        created_at=comment_date
                    )
                    
                    source.total_comments += 1
                except Exception as e:
                    logger.error(f"Error processing comment {comment.get('id')}: {str(e)}")
                    continue

            # Update source statistics
            source.total_posts += 1
            source.total_reactions += post.get('reactions', {}).get('summary', {}).get('total_count', 0)
        
        source.matching_posts = matching_count
        source.last_fetched = timezone.now()
        source.save()
        logger.info(f"Completed processing. Total posts: {source.indexed_posts}, Matching posts: {matching_count}")
        return None  # No error

class TwitterService:
    def __init__(self):
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            logger.error("TWITTER_BEARER_TOKEN environment variable is not set")
            raise ValueError("TWITTER_BEARER_TOKEN environment variable is not set")
            
        self.base_url = 'https://api.twitter.com/2'
        self.headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        logger.info("TwitterService initialized")
        # Log token info (first few characters only for security)
        logger.info(f"Using token starting with: {self.bearer_token[:10]}...")

    def validate_token(self):
        """Validate the bearer token before making requests."""
        try:
            # Try to fetch user info to validate token
            user_url = f"{self.base_url}/users/me"
            response = requests.get(user_url, headers=self.headers)
            
            if response.status_code == 200:
                logger.info("Twitter token validated successfully")
                return True
            else:
                logger.error(f"Token validation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False

    def get_user_tweets(self, username, max_results=100):
        """Fetch recent tweets from a Twitter username."""
        try:
            # Validate token first
            if not self.validate_token():
                raise Exception("Invalid or expired bearer token")

            # First, get the user ID from the username
            user_url = f"{self.base_url}/users/by/username/{username}"
            
            # Print complete request details for Postman testing
            print("\n=== Complete Request Details for Postman (User Lookup) ===")
            print(f"Method: GET")
            print(f"URL: {user_url}")
            print(f"Headers: {json.dumps(self.headers, indent=2)}")
            print("Query Params: None")
            print("=== End Request Details ===\n")

            # Also log it
            logger.info("=== Complete Request Details for Postman (User Lookup) ===")
            logger.info(f"Method: GET")
            logger.info(f"URL: {user_url}")
            logger.info(f"Headers: {json.dumps(self.headers, indent=2)}")
            logger.info("Query Params: None")
            logger.info("=== End Request Details ===")
            
            user_response = requests.get(user_url, headers=self.headers)
            print(f"Response status code: {user_response.status_code}")
            
            try:
                response_data = user_response.json()
                print(f"Response data: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response text: {user_response.text}")
                logger.error(f"Invalid JSON response: {user_response.text}")
                return []
            
            if user_response.status_code != 200:
                logger.error(f"Error fetching user ID: {user_response.status_code} - {user_response.text}")
                return []
            
            if not response_data or 'data' not in response_data:
                logger.error(f"No user data found for username: {username}")
                return []
            
            user_id = response_data['data']['id']
            logger.info(f"Found user ID: {user_id} for username: {username}")
            
            # Now fetch the user's tweets
            tweets_url = f"{self.base_url}/users/{user_id}/tweets"
            params = {
                'max_results': max_results,
                'tweet.fields': 'created_at,public_metrics,text',
                'expansions': 'author_id'
            }
            
            # Print complete request details for Postman testing
            print("\n=== Complete Request Details for Postman (Tweets Fetch) ===")
            print(f"Method: GET")
            print(f"URL: {tweets_url}")
            print(f"Headers: {json.dumps(self.headers, indent=2)}")
            print(f"Query Params: {json.dumps(params, indent=2)}")
            print("=== End Request Details ===\n")

            # Also log it
            logger.info("=== Complete Request Details for Postman (Tweets Fetch) ===")
            logger.info(f"Method: GET")
            logger.info(f"URL: {tweets_url}")
            logger.info(f"Headers: {json.dumps(self.headers, indent=2)}")
            logger.info(f"Query Params: {json.dumps(params, indent=2)}")
            logger.info("=== End Request Details ===")
            
            tweets_response = requests.get(tweets_url, headers=self.headers, params=params)
            print(f"Response status code: {tweets_response.status_code}")
            
            try:
                tweets_data = tweets_response.json()
                print(f"Response data: {json.dumps(tweets_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response text: {tweets_response.text}")
                logger.error(f"Invalid JSON response: {tweets_response.text}")
                return []
            
            if tweets_response.status_code != 200:
                logger.error(f"Error fetching tweets: {tweets_response.status_code} - {tweets_response.text}")
                return []
            
            if not tweets_data or 'data' not in tweets_data:
                logger.info(f"No tweets found for user: {username}")
                return []
            
            tweets = tweets_data['data']
            logger.info(f"Successfully fetched {len(tweets)} tweets for user: {username}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error in get_user_tweets: {str(e)}")
            return []

    def process_tweets(self, source, survey):
        """Process tweets and create social media responses."""
        try:
            logger.info(f"Processing tweets for source: {source.source_id}")
            source.total_pull_requests += 1
            
            # Fetch tweets
            tweets = self.get_user_tweets(source.source_id)
            if not tweets:
                source.failed_pull_requests += 1
                source.last_error = "No tweets found or error fetching tweets"
                source.save()
                return
            
            source.successful_pull_requests += 1
            source.indexed_posts = len(tweets)
            
            # Convert survey end date to naive datetime for comparison
            if timezone.is_aware(survey.end_date):
                survey_end = timezone.make_naive(survey.end_date)
            else:
                survey_end = survey.end_date
            
            # Get topics from source instead of survey
            topics = [topic.strip().lower() for topic in source.topics.split(',')]
            logger.info(f"Monitoring topics: {topics}")
            
            # Process each tweet
            matching_posts = 0
            for tweet in tweets:
                try:
                    tweet_date = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    
                    # Skip if tweet is after survey end date
                    if tweet_date > survey_end:
                        continue
                    
                    # Check if response already exists
                    if SocialMediaResponse.objects.filter(survey=survey, source_id=tweet['id']).exists():
                        logger.info(f"Response already exists for tweet {tweet['id']}, skipping")
                        continue
                    
                    # Analyze tweet text
                    analysis = analyze_text(tweet['text'])
                    
                    # Check if tweet matches any topics
                    if any(topic in tweet['text'].lower() for topic in topics):
                        matching_posts += 1
                        
                        # Create social media response
                        response = SocialMediaResponse.objects.create(
                            survey=survey,
                            source_type='twitter',
                            source_id=tweet['id'],
                            text=tweet['text'],
                            sentiment_score=analysis.get('sentiment_scores', {}).get('compound', 0.0),
                            sentiment_label=analysis.get('sentiment', 'neutral'),
                            topics=analysis.get('topics', []),
                            entities=analysis.get('entities', []),
                            created_at=tweet_date
                        )
                        
                        # Update engagement metrics
                        metrics = tweet.get('public_metrics', {})
                        source.total_posts += 1
                        source.total_comments += metrics.get('reply_count', 0)
                        source.total_reactions += metrics.get('like_count', 0) + metrics.get('retweet_count', 0)
                except Exception as e:
                    logger.error(f"Error processing tweet: {str(e)}")
                    continue
            
            source.matching_posts = matching_posts
            source.last_fetched = timezone.now()
            source.last_error = None
            source.save()
            
            logger.info(f"Successfully processed {matching_posts} matching tweets for source: {source.source_id}")
            
        except Exception as e:
            logger.error(f"Error in process_tweets: {str(e)}")
            source.failed_pull_requests += 1
            source.last_error = str(e)
            source.save()

def start_survey_collection(survey):
    """Start collecting data from all social media sources for a survey."""
    try:
        logger.info(f"Starting survey collection for survey: {survey.title}")
        
        sources = SocialMediaSource.objects.filter(survey=survey, is_active=True)
        logger.info(f"Found {sources.count()} active sources")
        
        error_messages = []
        
        for source in sources:
            try:
                logger.info(f"Processing source: {source.source_name} ({source.platform})")
                
                # Validate source has required fields
                if not source.source_id:
                    error_msg = f"Source {source.source_name} has no source_id"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    continue
                    
                if source.platform == 'facebook':
                    try:
                        service = FacebookService(source)
                        error_message = service.process_posts(source, survey)
                        if error_message:
                            error_messages.append(f"{source.source_name}: {error_message}")
                    except ValueError as e:
                        error_msg = f"Failed to initialize Facebook service: {str(e)}"
                        logger.error(error_msg)
                        error_messages.append(f"{source.source_name}: {error_msg}")
                        source.failed_pull_requests += 1
                        source.last_error = str(e)
                        source.save()
                elif source.platform == 'twitter':
                    try:
                        service = TwitterService()
                        service.process_tweets(source, survey)
                    except ValueError as e:
                        error_msg = f"Failed to initialize Twitter service: {str(e)}"
                        logger.error(error_msg)
                        error_messages.append(f"{source.source_name}: {error_msg}")
                        source.failed_pull_requests += 1
                        source.last_error = str(e)
                        source.save()
                else:
                    error_msg = f"Unsupported platform: {source.platform}"
                    logger.error(error_msg)
                    error_messages.append(f"{source.source_name}: {error_msg}")
                    continue
                    
            except Exception as e:
                error_msg = f"Error processing source {source.source_name}: {str(e)}"
                logger.error(error_msg)
                error_messages.append(f"{source.source_name}: {error_msg}")
                source.failed_pull_requests += 1
                source.last_error = str(e)
                source.save()
                continue
        
        #send questions if any
        questions_set = Question.objects.filter(survey = survey)
        if questions_set.exists():
            location = Location.objects.filter(id = survey.project.location_id).first()
            consituencies = get_constituencies_under(location)
            respondents = Volunteers.objects.filter(location_id__in=consituencies)
            send_questions(respondents, questions_set)

            
        # Return error messages if any occurred
        if error_messages:
            return "\n".join(error_messages)
        return None
                
    except Exception as e:
        error_msg = f"Error in start_survey_collection: {str(e)}"
        logger.error(error_msg)
        return error_msg 
    
def get_constituencies_under(location):
    if location.location_type == 'Constituency':
        return Location.objects.filter(id=location.id)

    elif location.location_type == 'District':
        return Location.objects.filter(parent=location, location_type='constituency')

    elif location.location_type == 'Region':
        return Location.objects.filter(parent__parent=location, location_type='constituency')

    elif location.location_type == 'National':
        return Location.objects.filter(parent__parent__parent=location, location_type='constituency')
    

def send_questions(respondents, questions):
    url = "https://telcomw.com/api-v2/send"
    api_key = "zhqkxkqadq3ik1gKWoaw"
    passcode = "Beautypt7897"
    for question in questions:
        dict = {}
        for respondent in respondents:
            dict[respondent.phone_number]=question.text
            print(question, respondent)
            payload = {
                "api_key": api_key,
                "numbers": "true",
                "from": 'Nutread-A1',
                "text": json.dumps(dict),  # Convert batch to JSON
                "password": passcode,
                "advance": "true"
            }
            print(f"Sending batch: {dict} messages")
            try:
                response = requests.post(url, data=payload)
                print("Log this", response.json())
            except Exception as e:
                logging.error(f"Failed to send SMS batch: {e}")


    # class NotificationService:
    # def __init__(self, from_, api_key, passcode):
    #     self.from_ = from_
    #     self.api_key = api_key
    #     self.passcode = passcode
    
    # def send_notification(self, messages_dict, batch_size=500, type = "ServiceNotification"):
    #     """
    #     Sends SMS notifications in batches.

    #     :param messages_dict: A dictionary where keys are phone numbers and values are message texts.
    #     :param batch_size: The number of messages to send per batch (default: 500).
    #     """
    #     url = "https://telcomw.com/api-v2/send"

    #     def batched(iterable, size):
    #         """Helper function to split a dictionary into chunks of given size"""
    #         iterator = iter(iterable)
    #         while batch := dict(islice(iterator, size)):  
    #             yield batch

    #     for batch in batched(messages_dict.items(), batch_size):
    #         payload = {
    #             "api_key": self.api_key,
    #             "numbers": "true",
    #             "from": self.from_,
    #             "text": json.dumps(dict(batch)),  # Convert batch to JSON
    #             "password": self.passcode,
    #             "advance": "true"
    #         }
    #         print(f"Sending batch: {len(batch)} messages")
    #         try:
    #             response = requests.post(url, data=payload)
    #             print(self.analytics_LogMessages(response, message_type=type))
    #         except Exception as e:
    #             logging.error(f"Failed to send SMS batch: {e}")
