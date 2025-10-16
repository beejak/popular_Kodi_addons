"""RSS feed collector for web mentions."""

from datetime import datetime, timedelta
import feedparser
from scripts.config import RSS_FEEDS
from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_rss_mentions(repositories):
    """
    Collect blog/article mentions from RSS feeds.

    Args:
        repositories: List of repository dictionaries from GitHub/GitLab collectors

    Returns:
        dict: Dictionary mapping repo_url to web mention count
              {repo_url: {'web_mentions': int}}
    """
    try:
        logger.info("Starting RSS feed collection...")

        # Prepare mention data dictionary
        rss_data = {}

        # Calculate 7-day cutoff (only look at recent entries)
        seven_days_ago = datetime.now() - timedelta(days=7)

        # Fetch each RSS feed
        for feed_url in RSS_FEEDS:
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(f"RSS feed may be malformed: {feed_url}")

                logger.info(f"Found {len(feed.entries)} entries in feed")

                # Process each entry
                for entry in feed.entries:
                    try:
                        # Check if entry is recent (last 7 days)
                        entry_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            entry_date = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                            entry_date = datetime(*entry.updated_parsed[:6])

                        # Skip old entries
                        if entry_date and entry_date < seven_days_ago:
                            continue

                        # Get entry content
                        content = ''
                        if hasattr(entry, 'title'):
                            content += entry.title + ' '
                        if hasattr(entry, 'summary'):
                            content += entry.summary + ' '
                        if hasattr(entry, 'description'):
                            content += entry.description + ' '

                        content = content.lower()

                        # Search for repository mentions
                        for repo in repositories:
                            repo_url = repo['repo_url']
                            repo_name = repo['name'].lower()
                            repo_owner = repo['owner'].lower()

                            # Check if content mentions this repository
                            mentioned = False
                            if repo_url.lower() in content:
                                mentioned = True
                            elif repo_name in content:
                                mentioned = True
                            elif f"{repo_owner}/{repo_name}" in content:
                                mentioned = True

                            if mentioned:
                                # Increment mention count
                                if repo_url not in rss_data:
                                    rss_data[repo_url] = {'web_mentions': 0}
                                rss_data[repo_url]['web_mentions'] += 1

                    except Exception as e:
                        logger.debug(f"Error processing RSS entry: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Could not fetch RSS feed {feed_url}: {e}")
                continue

        # Fill in zeros for repositories with no mentions
        for repo in repositories:
            repo_url = repo['repo_url']
            if repo_url not in rss_data:
                rss_data[repo_url] = {'web_mentions': 0}

        # Count how many repos had mentions
        repos_with_mentions = sum(1 for data in rss_data.values() if data['web_mentions'] > 0)
        logger.info(f"RSS collection complete. Found mentions for {repos_with_mentions}/{len(repositories)} repositories")

        return rss_data

    except Exception as e:
        logger.error(f"Fatal error in RSS collector: {e}")
        # Return empty dict for all repos
        return {repo['repo_url']: {'web_mentions': 0} for repo in repositories}
