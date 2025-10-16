"""CSV file generator for snapshots and tier data."""

import csv
import os
from datetime import datetime
from pathlib import Path
from scripts.config import REPO_ROOT, SNAPSHOTS_DIR, CURRENT_DIR
from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_snapshot_csv(all_repos, date_str=None):
    """
    Generate weekly snapshot CSV with all repositories.

    Args:
        all_repos: List of all repository dictionaries
        date_str: Date string (YYYY-MM-DD). If None, uses current date.
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    logger.info(f"Generating snapshot CSV for {date_str}...")

    # Create snapshots directory if it doesn't exist
    snapshots_path = Path(REPO_ROOT) / SNAPSHOTS_DIR
    snapshots_path.mkdir(parents=True, exist_ok=True)

    # CSV file path
    csv_file = snapshots_path / f"snapshot_{date_str}.csv"

    # CSV columns (matching schema from planning.md)
    columns = [
        'repo_url',
        'platform',
        'name',
        'owner',
        'stars',
        'forks',
        'last_commit_date',
        'created_date',
        'age_days',
        'issues_count',
        'has_recent_activity',
        'reddit_mentions',
        'reddit_upvotes',
        'web_mentions',
        'tier',
        'rank_in_tier',
        'star_velocity_30d',
        'snapshot_date'
    ]

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for repo in all_repos:
                row = {
                    'repo_url': repo.get('repo_url', ''),
                    'platform': repo.get('platform', ''),
                    'name': repo.get('name', ''),
                    'owner': repo.get('owner', ''),
                    'stars': repo.get('stars', 0),
                    'forks': repo.get('forks', 0),
                    'last_commit_date': repo.get('last_commit_date', ''),
                    'created_date': repo.get('created_date', ''),
                    'age_days': repo.get('age_days', 0),
                    'issues_count': repo.get('open_issues', 0),
                    'has_recent_activity': repo.get('has_recent_activity', False),
                    'reddit_mentions': repo.get('reddit_mentions', 0),
                    'reddit_upvotes': repo.get('reddit_upvotes', 0),
                    'web_mentions': repo.get('web_mentions', 0),
                    'tier': repo.get('tier', ''),
                    'rank_in_tier': repo.get('rank_in_tier', 0),
                    'star_velocity_30d': repo.get('star_velocity_30d', 0),
                    'snapshot_date': date_str
                }
                writer.writerow(row)

        logger.info(f"Snapshot CSV saved: {csv_file} ({len(all_repos)} repositories)")

    except Exception as e:
        logger.error(f"Error generating snapshot CSV: {e}")
        raise


def generate_tier_csvs(established, rising, new):
    """
    Generate current tier CSV files.

    Args:
        established: List of established tier repositories
        rising: List of rising tier repositories
        new: List of new tier repositories
    """
    logger.info("Generating tier CSV files...")

    # Create current directory if it doesn't exist
    current_path = Path(REPO_ROOT) / CURRENT_DIR
    current_path.mkdir(parents=True, exist_ok=True)

    # CSV columns (same as snapshot)
    columns = [
        'repo_url',
        'platform',
        'name',
        'owner',
        'stars',
        'forks',
        'last_commit_date',
        'created_date',
        'age_days',
        'issues_count',
        'has_recent_activity',
        'reddit_mentions',
        'reddit_upvotes',
        'web_mentions',
        'tier',
        'rank_in_tier',
        'star_velocity_30d',
        'snapshot_date'
    ]

    date_str = datetime.now().strftime('%Y-%m-%d')

    # Generate each tier file
    tiers = {
        'established': established,
        'rising': rising,
        'new': new
    }

    for tier_name, repos in tiers.items():
        csv_file = current_path / f"{tier_name}.csv"

        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

                for repo in repos:
                    row = {
                        'repo_url': repo.get('repo_url', ''),
                        'platform': repo.get('platform', ''),
                        'name': repo.get('name', ''),
                        'owner': repo.get('owner', ''),
                        'stars': repo.get('stars', 0),
                        'forks': repo.get('forks', 0),
                        'last_commit_date': repo.get('last_commit_date', ''),
                        'created_date': repo.get('created_date', ''),
                        'age_days': repo.get('age_days', 0),
                        'issues_count': repo.get('open_issues', 0),
                        'has_recent_activity': repo.get('has_recent_activity', False),
                        'reddit_mentions': repo.get('reddit_mentions', 0),
                        'reddit_upvotes': repo.get('reddit_upvotes', 0),
                        'web_mentions': repo.get('web_mentions', 0),
                        'tier': repo.get('tier', ''),
                        'rank_in_tier': repo.get('rank_in_tier', 0),
                        'star_velocity_30d': repo.get('star_velocity_30d', 0),
                        'snapshot_date': date_str
                    }
                    writer.writerow(row)

            logger.info(f"Tier CSV saved: {csv_file} ({len(repos)} repositories)")

        except Exception as e:
            logger.error(f"Error generating {tier_name} tier CSV: {e}")
            raise

    logger.info("All tier CSV files generated successfully")
