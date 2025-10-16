"""GitLab repository data collector."""

import os
from datetime import datetime, timedelta
import gitlab
from scripts.config import (
    SEARCH_KEYWORDS, MIN_STARS, ACTIVITY_MONTHS,
    POC_MODE, POC_LIMIT, API_TIMEOUT
)
from scripts.utils.logger import setup_logger
from scripts.utils.date_utils import calculate_age_days, format_date_iso, parse_date

logger = setup_logger(__name__)


def collect_gitlab_repos():
    """
    Collect repository data from GitLab API.

    Returns:
        list: List of repository dictionaries with standardized structure.
              Returns empty list on failure.
    """
    try:
        # Get GitLab token from environment
        gitlab_token = os.getenv('GITLAB_TOKEN')
        if not gitlab_token:
            logger.warning("GITLAB_TOKEN not found in environment variables. Skipping GitLab collection.")
            return []

        # Initialize GitLab API client
        logger.info("Initializing GitLab API client...")
        gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_token, timeout=API_TIMEOUT)

        # Authenticate
        try:
            gl.auth()
            logger.info("GitLab authentication successful")
        except gitlab.exceptions.GitlabAuthenticationError as e:
            logger.error(f"GitLab authentication failed: {e}")
            return []

        # Collect repositories
        repos_data = []
        seen_repos = set()

        # Calculate activity cutoff date
        activity_cutoff = datetime.now() - timedelta(days=ACTIVITY_MONTHS * 30)

        # Search with simplified keywords (GitLab search is more limited)
        search_terms = ["kodi addon", "kodi plugin", "xbmc"]

        for search_term in search_terms:
            if POC_MODE and len(repos_data) >= POC_LIMIT:
                logger.info(f"POC mode: Reached limit of {POC_LIMIT} repositories")
                break

            try:
                logger.info(f"Searching GitLab for: {search_term}")

                # Search projects
                projects = gl.projects.list(
                    search=search_term,
                    order_by='star_count',
                    sort='desc',
                    archived=False,
                    get_all=False,
                    per_page=50
                )

                for project in projects:
                    if POC_MODE and len(repos_data) >= POC_LIMIT:
                        break

                    # Skip if already seen
                    if project.path_with_namespace in seen_repos:
                        continue

                    try:
                        # Apply filters
                        star_count = getattr(project, 'star_count', 0)
                        if star_count < MIN_STARS:
                            logger.debug(f"Skipping project with few stars: {project.path_with_namespace} ({star_count} stars)")
                            continue

                        # Check for recent activity
                        last_activity_at = parse_date(project.last_activity_at)
                        has_recent_activity = last_activity_at and last_activity_at > activity_cutoff

                        if not has_recent_activity:
                            logger.debug(f"Skipping inactive project: {project.path_with_namespace}")
                            continue

                        # Fetch contributors (top 3)
                        contributors = []
                        try:
                            contrib_list = project.repository_contributors(get_all=False, per_page=3)
                            contributors = [c['name'] for c in contrib_list if 'name' in c]
                        except Exception as e:
                            logger.warning(f"Could not fetch contributors for {project.path_with_namespace}: {e}")
                            # Use owner as fallback
                            if hasattr(project, 'namespace') and hasattr(project.namespace, 'name'):
                                contributors = [project.namespace['name']]

                        # Get created date
                        created_at = parse_date(project.created_at) if hasattr(project, 'created_at') else None

                        # Build standardized data structure
                        repo_data = {
                            'platform': 'gitlab',
                            'repo_url': project.web_url,
                            'name': project.name,
                            'owner': project.namespace['name'] if hasattr(project, 'namespace') else 'Unknown',
                            'stars': star_count,
                            'forks': getattr(project, 'forks_count', 0),
                            'description': getattr(project, 'description', '') or '',
                            'created_date': format_date_iso(created_at),
                            'last_commit_date': format_date_iso(last_activity_at),
                            'last_activity_date': format_date_iso(last_activity_at),
                            'age_days': calculate_age_days(created_at) if created_at else 0,
                            'is_archived': getattr(project, 'archived', False),
                            'is_fork': False,  # GitLab doesn't easily expose fork status
                            'open_issues': getattr(project, 'open_issues_count', 0),
                            'contributors': contributors if contributors else ['Unknown'],
                            'has_recent_activity': has_recent_activity,
                            'recent_commits_count': 0  # Would require additional API calls
                        }

                        repos_data.append(repo_data)
                        seen_repos.add(project.path_with_namespace)
                        logger.info(f"Added project: {project.path_with_namespace} ({star_count} stars)")

                    except Exception as e:
                        logger.error(f"Error processing project {project.path_with_namespace}: {e}")
                        continue

            except gitlab.exceptions.GitlabError as e:
                logger.error(f"GitLab API error for search term '{search_term}': {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error searching for '{search_term}': {e}")
                continue

        logger.info(f"GitLab collection complete. Found {len(repos_data)} repositories")
        return repos_data

    except Exception as e:
        logger.error(f"Fatal error in GitLab collector: {e}")
        return []
