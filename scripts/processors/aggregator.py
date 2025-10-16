"""Data aggregator to combine data from all sources."""

from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def aggregate_data(github_repos, gitlab_repos, bitbucket_repos, reddit_data, rss_data):
    """
    Combine data from all sources into unified dataset.

    Args:
        github_repos: List of repositories from GitHub
        gitlab_repos: List of repositories from GitLab
        bitbucket_repos: List of repositories from Bitbucket
        reddit_data: Dictionary mapping repo_url to Reddit metrics
        rss_data: Dictionary mapping repo_url to RSS mention counts

    Returns:
        list: Unified list of repositories with social signals merged
    """
    logger.info("Starting data aggregation...")

    # Combine all repositories
    all_repos = []
    all_repos.extend(github_repos)
    all_repos.extend(gitlab_repos)
    all_repos.extend(bitbucket_repos)

    logger.info(f"Combined {len(all_repos)} repositories from all platforms")

    # Deduplicate repositories
    # Strategy: If same repo on multiple platforms, keep the one with more stars
    deduplicated = _deduplicate_repos(all_repos)

    logger.info(f"After deduplication: {len(deduplicated)} unique repositories")

    # Merge social signals
    for repo in deduplicated:
        repo_url = repo['repo_url']

        # Merge Reddit data
        if repo_url in reddit_data:
            repo['reddit_mentions'] = reddit_data[repo_url].get('reddit_mentions', 0)
            repo['reddit_upvotes'] = reddit_data[repo_url].get('reddit_upvotes', 0)
            repo['recent_mentions_30d'] = reddit_data[repo_url].get('recent_mentions_30d', 0)
        else:
            repo['reddit_mentions'] = 0
            repo['reddit_upvotes'] = 0
            repo['recent_mentions_30d'] = 0

        # Merge RSS data
        if repo_url in rss_data:
            repo['web_mentions'] = rss_data[repo_url].get('web_mentions', 0)
        else:
            repo['web_mentions'] = 0

    logger.info("Social signals merged successfully")

    return deduplicated


def _deduplicate_repos(repos):
    """
    Remove duplicate repositories across platforms.

    If the same addon appears on multiple platforms (e.g., GitHub and GitLab),
    keep the one with more stars.

    Args:
        repos: List of repository dictionaries

    Returns:
        list: Deduplicated list of repositories
    """
    # Group by name + owner
    repo_groups = {}

    for repo in repos:
        # Create a key based on name and owner (case-insensitive)
        key = f"{repo['owner'].lower()}/{repo['name'].lower()}"

        if key not in repo_groups:
            repo_groups[key] = []

        repo_groups[key].append(repo)

    # For each group, keep the one with most stars
    deduplicated = []

    for key, group in repo_groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Multiple platforms - keep the one with most stars
            best_repo = max(group, key=lambda r: r['stars'])
            logger.info(f"Deduplicating {key}: keeping {best_repo['platform']} version with {best_repo['stars']} stars")
            deduplicated.append(best_repo)

    return deduplicated
