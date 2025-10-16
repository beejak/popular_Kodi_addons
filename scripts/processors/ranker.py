"""Repository ranking and tier classification."""

from scripts.config import (
    TIER_AGE_THRESHOLDS,
    ESTABLISHED_WEIGHTS,
    RISING_WEIGHTS,
    NEW_WEIGHTS,
    GROWTH_THRESHOLDS
)
from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def classify_and_rank(repositories):
    """
    Classify repositories into tiers and rank within tiers.

    Args:
        repositories: List of repository dictionaries

    Returns:
        tuple: Three lists (established, rising, new) sorted by rank
    """
    logger.info(f"Starting classification and ranking of {len(repositories)} repositories...")

    # Classify into tiers
    established = []
    rising = []
    new = []

    for repo in repositories:
        age_days = repo['age_days']

        # Determine tier based on age
        if age_days < TIER_AGE_THRESHOLDS['new']:
            # New tier (< 3 months)
            tier = 'new'
            new.append(repo)
        elif age_days < TIER_AGE_THRESHOLDS['rising']:
            # Rising tier (3-12 months)
            # Check if it has growth signals
            if _has_growth_signals(repo):
                tier = 'rising'
                rising.append(repo)
            else:
                # No growth signals, classify as established
                tier = 'established'
                established.append(repo)
        else:
            # Established tier (12+ months)
            tier = 'established'
            established.append(repo)

        repo['tier'] = tier

    logger.info(f"Classification complete: {len(established)} established, {len(rising)} rising, {len(new)} new")

    # Calculate scores and rank within each tier
    established_ranked = _rank_tier(established, 'established')
    rising_ranked = _rank_tier(rising, 'rising')
    new_ranked = _rank_tier(new, 'new')

    return established_ranked, rising_ranked, new_ranked


def _has_growth_signals(repo):
    """
    Check if repository shows growth signals for Rising tier classification.

    Growth signals:
    - Star velocity > threshold
    - Increased commit frequency
    - Rising Reddit mentions
    - Web mentions present

    Args:
        repo: Repository dictionary

    Returns:
        bool: True if repo has growth signals
    """
    # Check star velocity (if available)
    star_velocity = repo.get('star_velocity_30d', 0)
    if star_velocity > GROWTH_THRESHOLDS['star_velocity_per_month']:
        return True

    # Check Reddit mentions (recent activity)
    recent_mentions = repo.get('recent_mentions_30d', 0)
    if recent_mentions > 0:
        return True

    # Check web mentions
    web_mentions = repo.get('web_mentions', 0)
    if web_mentions > 0:
        return True

    # Check commit activity (if repo has high recent activity)
    recent_commits = repo.get('recent_commits_count', 0)
    if recent_commits > 10:  # At least 10 commits in last 6 months shows activity
        return True

    return False


def _rank_tier(repos, tier_name):
    """
    Calculate scores and rank repositories within a tier.

    Args:
        repos: List of repositories in this tier
        tier_name: Name of tier ('established', 'rising', 'new')

    Returns:
        list: Sorted list of repositories with rank_in_tier assigned
    """
    if not repos:
        return []

    logger.info(f"Ranking {len(repos)} repositories in {tier_name} tier...")

    # Select weights based on tier
    if tier_name == 'established':
        weights = ESTABLISHED_WEIGHTS
    elif tier_name == 'rising':
        weights = RISING_WEIGHTS
    else:  # new
        weights = NEW_WEIGHTS

    # Calculate composite score for each repo
    for repo in repos:
        score = _calculate_score(repo, weights, tier_name)
        repo['composite_score'] = score

    # Sort by score (descending)
    repos_sorted = sorted(repos, key=lambda r: r['composite_score'], reverse=True)

    # Assign rank within tier
    for i, repo in enumerate(repos_sorted):
        repo['rank_in_tier'] = i + 1

    logger.info(f"Ranking complete for {tier_name} tier")

    return repos_sorted


def _calculate_score(repo, weights, tier_name):
    """
    Calculate composite score based on weighted factors.

    Args:
        repo: Repository dictionary
        weights: Dictionary of weights for each factor
        tier_name: Name of tier

    Returns:
        float: Composite score
    """
    score = 0.0

    # Stars component (normalized)
    if 'stars' in weights:
        # Log scale for stars to prevent very popular repos from dominating
        stars = repo.get('stars', 0)
        stars_score = _log_scale(stars, 20, 10000) * weights['stars']
        score += stars_score

    # Recent activity component
    if 'recent_activity' in weights:
        recent_commits = repo.get('recent_commits_count', 0)
        activity_score = _log_scale(recent_commits, 1, 100) * weights['recent_activity']
        score += activity_score

    # Social signals component
    if 'social_signals' in weights:
        reddit_mentions = repo.get('reddit_mentions', 0)
        reddit_upvotes = repo.get('reddit_upvotes', 0)
        web_mentions = repo.get('web_mentions', 0)

        # Combined social score
        social_score = (
            _log_scale(reddit_mentions, 0, 50) * 0.4 +
            _log_scale(reddit_upvotes, 0, 500) * 0.4 +
            _log_scale(web_mentions, 0, 10) * 0.2
        ) * weights['social_signals']

        score += social_score

    # Growth rate component (for rising tier)
    if 'growth_rate' in weights:
        star_velocity = repo.get('star_velocity_30d', 0)
        recent_mentions = repo.get('recent_mentions_30d', 0)

        growth_score = (
            _log_scale(star_velocity, 0, 100) * 0.6 +
            _log_scale(recent_mentions, 0, 20) * 0.4
        ) * weights['growth_rate']

        score += growth_score

    return score


def _log_scale(value, min_val, max_val):
    """
    Normalize value to 0-1 scale using logarithmic scaling.

    Args:
        value: Value to normalize
        min_val: Minimum expected value
        max_val: Maximum expected value

    Returns:
        float: Normalized value between 0 and 1
    """
    import math

    if value <= min_val:
        return 0.0

    if value >= max_val:
        return 1.0

    # Logarithmic scaling
    # Shift values to start at 1 for log calculation
    shifted_val = value - min_val + 1
    shifted_max = max_val - min_val + 1

    normalized = math.log(shifted_val) / math.log(shifted_max)

    return max(0.0, min(1.0, normalized))
