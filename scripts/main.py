"""Main orchestration script for Kodi Repository Tracker."""

import sys
import json
from datetime import datetime
from pathlib import Path

from scripts.config import POC_MODE, REPO_ROOT, RAW_DIR
from scripts.utils.logger import setup_logger

# Collectors
from scripts.collectors.github_collector import collect_github_repos
from scripts.collectors.gitlab_collector import collect_gitlab_repos
from scripts.collectors.bitbucket_collector import collect_bitbucket_repos
from scripts.collectors.reddit_collector import collect_reddit_data
from scripts.collectors.rss_collector import collect_rss_mentions

# Processors
from scripts.processors.aggregator import aggregate_data
from scripts.processors.ranker import classify_and_rank

# Generators
from scripts.generators.csv_generator import generate_snapshot_csv, generate_tier_csvs
from scripts.generators.readme_generator import generate_readme


def main():
    """Main entry point for the Kodi Repository Tracker."""
    logger = setup_logger()

    logger.info("=" * 60)
    logger.info("Kodi Repository Tracker - Starting")
    logger.info(f"Mode: {'POC (limited to 10 repos)' if POC_MODE else 'Production'}")
    logger.info("=" * 60)

    date_str = datetime.now().strftime('%Y-%m-%d')

    try:
        # Step 1: Collect data from all sources
        logger.info("\n--- STEP 1: Data Collection ---")

        # GitHub (critical - must succeed)
        logger.info("Collecting from GitHub...")
        github_repos = collect_github_repos()

        if not github_repos:
            logger.error("CRITICAL: GitHub collection failed and returned no data")
            logger.error("Cannot continue without GitHub data")
            sys.exit(1)

        logger.info(f"GitHub collection successful: {len(github_repos)} repositories")

        # GitLab (optional)
        logger.info("Collecting from GitLab...")
        gitlab_repos = collect_gitlab_repos()
        logger.info(f"GitLab collection: {len(gitlab_repos)} repositories")

        # Bitbucket (optional, stub for now)
        logger.info("Collecting from Bitbucket...")
        bitbucket_repos = collect_bitbucket_repos()
        logger.info(f"Bitbucket collection: {len(bitbucket_repos)} repositories")

        # Combine repos for social signal collection
        all_repos_for_social = github_repos + gitlab_repos + bitbucket_repos

        # Reddit (optional)
        logger.info("Collecting social signals from Reddit...")
        reddit_data = collect_reddit_data(all_repos_for_social)
        logger.info(f"Reddit collection: {len(reddit_data)} repositories with data")

        # RSS (optional)
        logger.info("Collecting web mentions from RSS feeds...")
        rss_data = collect_rss_mentions(all_repos_for_social)
        logger.info(f"RSS collection: {len(rss_data)} repositories with data")

        # Save raw data
        _save_raw_data(github_repos, gitlab_repos, bitbucket_repos, reddit_data, rss_data, date_str)

        # Step 2: Aggregate and deduplicate data
        logger.info("\n--- STEP 2: Data Aggregation ---")
        aggregated_repos = aggregate_data(
            github_repos,
            gitlab_repos,
            bitbucket_repos,
            reddit_data,
            rss_data
        )

        logger.info(f"Aggregation complete: {len(aggregated_repos)} unique repositories")

        if not aggregated_repos:
            logger.warning("No repositories found after aggregation")
            # Still generate empty README
            generate_readme([], [], [], date_str)
            logger.info("Generated empty README")
            return

        # Step 3: Classify and rank
        logger.info("\n--- STEP 3: Classification and Ranking ---")
        established, rising, new = classify_and_rank(aggregated_repos)

        logger.info(f"Classification complete:")
        logger.info(f"  - Established: {len(established)} repositories")
        logger.info(f"  - Rising: {len(rising)} repositories")
        logger.info(f"  - New: {len(new)} repositories")

        # Step 4: Generate CSV files
        logger.info("\n--- STEP 4: CSV Generation ---")

        # Generate snapshot CSV (all repos)
        generate_snapshot_csv(aggregated_repos, date_str)

        # Generate tier CSVs
        generate_tier_csvs(established, rising, new)

        logger.info("CSV generation complete")

        # Step 5: Generate README
        logger.info("\n--- STEP 5: README Generation ---")
        generate_readme(established, rising, new, date_str)

        logger.info("README generation complete")

        # Step 6: Summary statistics
        logger.info("\n--- SUMMARY ---")
        logger.info(f"Total repositories processed: {len(aggregated_repos)}")
        logger.info(f"Established tier: {len(established)}")
        logger.info(f"Rising tier: {len(rising)}")
        logger.info(f"New tier: {len(new)}")

        # Count repos with social signals
        repos_with_reddit = sum(1 for r in aggregated_repos if r.get('reddit_mentions', 0) > 0)
        repos_with_web = sum(1 for r in aggregated_repos if r.get('web_mentions', 0) > 0)

        logger.info(f"Repositories with Reddit mentions: {repos_with_reddit}")
        logger.info(f"Repositories with web mentions: {repos_with_web}")

        logger.info("\n" + "=" * 60)
        logger.info("Kodi Repository Tracker - Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


def _save_raw_data(github_repos, gitlab_repos, bitbucket_repos, reddit_data, rss_data, date_str):
    """
    Save raw API responses to JSON files.

    Args:
        github_repos: List of GitHub repositories
        gitlab_repos: List of GitLab repositories
        bitbucket_repos: List of Bitbucket repositories
        reddit_data: Dictionary of Reddit data
        rss_data: Dictionary of RSS data
        date_str: Date string for filename
    """
    logger = setup_logger()

    # Create raw directory
    raw_path = Path(REPO_ROOT) / RAW_DIR
    raw_path.mkdir(parents=True, exist_ok=True)

    # Save each data source
    data_sources = {
        'github': github_repos,
        'gitlab': gitlab_repos,
        'bitbucket': bitbucket_repos,
        'reddit': reddit_data,
        'web_mentions': rss_data
    }

    for source_name, data in data_sources.items():
        filename = raw_path / f"{source_name}_{date_str}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Saved raw data: {filename}")

        except Exception as e:
            logger.warning(f"Could not save raw data for {source_name}: {e}")


if __name__ == '__main__':
    main()
