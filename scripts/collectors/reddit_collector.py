"""Reddit social signals collector."""

import os
import time
from datetime import datetime, timedelta
import praw
from prawcore.exceptions import ResponseException, RequestException
from scripts.config import SUBREDDITS, API_TIMEOUT
from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_reddit_data(repositories):
    """
    Collect Reddit mentions and upvotes for repositories.

    Args:
        repositories: List of repository dictionaries from GitHub/GitLab collectors

    Returns:
        dict: Dictionary mapping repo_url to Reddit metrics
              {repo_url: {'reddit_mentions': int, 'reddit_upvotes': int, 'recent_mentions_30d': int}}
    """
    try:
        # Get Reddit credentials from environment
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'KodiAddonTracker/1.0')

        if not client_id or not client_secret:
            logger.warning("Reddit credentials not found in environment variables. Skipping Reddit collection.")
            return {}

        # Initialize Reddit API client
        logger.info("Initializing Reddit API client...")
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            timeout=API_TIMEOUT
        )

        # Test authentication
        try:
            reddit.user.me()
        except Exception:
            # Read-only mode is fine for searching
            pass

        logger.info("Reddit API client initialized")

        # Prepare reddit data dictionary
        reddit_data = {}

        # Calculate 30-day cutoff for recent mentions
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Search for each repository
        for repo in repositories:
            repo_url = repo['repo_url']
            repo_name = repo['name']
            repo_owner = repo['owner']

            logger.info(f"Searching Reddit for: {repo_name}")

            mentions = 0
            total_upvotes = 0
            recent_mentions = 0

            # Search across configured subreddits
            for subreddit_name in SUBREDDITS:
                try:
                    subreddit = reddit.subreddit(subreddit_name)

                    # Search for repository URL
                    search_queries = [
                        repo_url,
                        repo_name,
                        f"{repo_owner}/{repo_name}"
                    ]

                    for query in search_queries:
                        try:
                            # Search posts
                            for submission in subreddit.search(query, time_filter='year', limit=50):
                                mentions += 1
                                total_upvotes += submission.score

                                # Check if recent (last 30 days)
                                submission_date = datetime.fromtimestamp(submission.created_utc)
                                if submission_date > thirty_days_ago:
                                    recent_mentions += 1

                            # Small delay to respect rate limits
                            time.sleep(0.5)

                        except Exception as e:
                            logger.debug(f"Error searching '{query}' in r/{subreddit_name}: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Could not access subreddit r/{subreddit_name}: {e}")
                    continue

            # Store results
            reddit_data[repo_url] = {
                'reddit_mentions': mentions,
                'reddit_upvotes': total_upvotes,
                'recent_mentions_30d': recent_mentions
            }

            if mentions > 0:
                logger.info(f"Found {mentions} Reddit mentions for {repo_name} (total upvotes: {total_upvotes})")

        logger.info(f"Reddit collection complete. Processed {len(repositories)} repositories")
        return reddit_data

    except ResponseException as e:
        logger.error(f"Reddit API response error: {e}")
        return {}
    except RequestException as e:
        logger.error(f"Reddit API request error: {e}")
        return {}
    except Exception as e:
        logger.error(f"Fatal error in Reddit collector: {e}")
        return {}
