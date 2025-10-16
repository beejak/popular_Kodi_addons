"""GitHub repository data collector."""

import os
from datetime import datetime, timedelta
from github import Github, GithubException
from scripts.config import (
    SEARCH_KEYWORDS, MIN_STARS, ACTIVITY_MONTHS,
    POC_MODE, POC_LIMIT, API_TIMEOUT
)
from scripts.utils.logger import setup_logger
from scripts.utils.date_utils import calculate_age_days, format_date_iso

logger = setup_logger(__name__)


def collect_github_repos():
    """
    Collect repository data from GitHub API.

    Returns:
        list: List of repository dictionaries with standardized structure.
              Returns empty list on failure.
    """
    try:
        # Get GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.error("GITHUB_TOKEN not found in environment variables")
            return []

        # Initialize GitHub API client
        logger.info("Initializing GitHub API client...")
        g = Github(github_token, timeout=API_TIMEOUT)

        # Check rate limit
        rate_limit = g.get_rate_limit()
        logger.info(f"GitHub API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")

        if rate_limit.core.remaining < 100:
            logger.warning(f"Low GitHub API rate limit: {rate_limit.core.remaining} remaining")

        # Collect repositories
        repos_data = []
        seen_repos = set()  # Track to avoid duplicates

        # Calculate activity cutoff date
        activity_cutoff = datetime.now() - timedelta(days=ACTIVITY_MONTHS * 30)

        # Search with each keyword
        for keyword in SEARCH_KEYWORDS:
            if POC_MODE and len(repos_data) >= POC_LIMIT:
                logger.info(f"POC mode: Reached limit of {POC_LIMIT} repositories")
                break

            try:
                logger.info(f"Searching GitHub for: {keyword}")

                # Search repositories, sort by stars
                query = f"{keyword} in:name,description,readme stars:>={MIN_STARS}"
                search_results = g.search_repositories(query=query, sort='stars', order='desc')

                # Process search results
                for repo in search_results:
                    if POC_MODE and len(repos_data) >= POC_LIMIT:
                        break

                    # Skip if already seen
                    if repo.full_name in seen_repos:
                        continue

                    try:
                        # Apply filters
                        if repo.archived:
                            logger.debug(f"Skipping archived repo: {repo.full_name}")
                            continue

                        if repo.stargazers_count < MIN_STARS:
                            logger.debug(f"Skipping repo with few stars: {repo.full_name} ({repo.stargazers_count} stars)")
                            continue

                        # Check for recent activity
                        has_recent_activity = False
                        last_activity_date = None

                        # Check last commit
                        if repo.pushed_at and repo.pushed_at > activity_cutoff:
                            has_recent_activity = True
                            last_activity_date = repo.pushed_at

                        # Check updated_at (includes issues, PRs, etc.)
                        if repo.updated_at and repo.updated_at > activity_cutoff:
                            has_recent_activity = True
                            if not last_activity_date or repo.updated_at > last_activity_date:
                                last_activity_date = repo.updated_at

                        if not has_recent_activity:
                            logger.debug(f"Skipping inactive repo: {repo.full_name}")
                            continue

                        # Fetch contributors (top 3)
                        contributors = []
                        try:
                            contrib_list = repo.get_contributors()
                            contributors = [c.login for c in contrib_list[:3]]
                        except GithubException as e:
                            logger.warning(f"Could not fetch contributors for {repo.full_name}: {e}")
                            contributors = [repo.owner.login]

                        # Count recent commits
                        recent_commits_count = 0
                        try:
                            commits = repo.get_commits(since=activity_cutoff)
                            recent_commits_count = commits.totalCount
                        except GithubException as e:
                            logger.warning(f"Could not fetch commits for {repo.full_name}: {e}")

                        # Build standardized data structure
                        repo_data = {
                            'platform': 'github',
                            'repo_url': repo.html_url,
                            'name': repo.name,
                            'owner': repo.owner.login,
                            'stars': repo.stargazers_count,
                            'forks': repo.forks_count,
                            'description': repo.description or '',
                            'created_date': format_date_iso(repo.created_at),
                            'last_commit_date': format_date_iso(repo.pushed_at),
                            'last_activity_date': format_date_iso(last_activity_date),
                            'age_days': calculate_age_days(repo.created_at),
                            'is_archived': repo.archived,
                            'is_fork': repo.fork,
                            'open_issues': repo.open_issues_count,
                            'contributors': contributors,
                            'has_recent_activity': has_recent_activity,
                            'recent_commits_count': recent_commits_count
                        }

                        repos_data.append(repo_data)
                        seen_repos.add(repo.full_name)
                        logger.info(f"Added repository: {repo.full_name} ({repo.stargazers_count} stars)")

                    except GithubException as e:
                        logger.error(f"Error processing repository {repo.full_name}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error processing repository: {e}")
                        continue

            except GithubException as e:
                if e.status == 403 and 'rate limit' in str(e).lower():
                    logger.error("GitHub API rate limit exceeded")
                    break
                else:
                    logger.error(f"GitHub API error for keyword '{keyword}': {e}")
                    continue
            except Exception as e:
                logger.error(f"Unexpected error searching for '{keyword}': {e}")
                continue

        logger.info(f"GitHub collection complete. Found {len(repos_data)} repositories")
        return repos_data

    except Exception as e:
        logger.error(f"Fatal error in GitHub collector: {e}")
        return []
