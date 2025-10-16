"""README.md generator with formatted tables."""

from datetime import datetime
from pathlib import Path
from scripts.config import REPO_ROOT
from scripts.utils.logger import setup_logger
from scripts.utils.date_utils import format_time_ago, parse_date

logger = setup_logger(__name__)


def generate_readme(established, rising, new, date_str=None):
    """
    Generate README.md with formatted tables for each tier.

    Args:
        established: List of established tier repositories
        rising: List of rising tier repositories
        new: List of new tier repositories
        date_str: Date string for last updated. If None, uses current date.
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    logger.info("Generating README.md...")

    readme_content = []

    # Header section
    readme_content.append("# Popular Kodi Addons")
    readme_content.append(f"*Last updated: {date_str}*")
    readme_content.append("")
    readme_content.append("A weekly curated list of popular Kodi addons discovered from GitHub, GitLab, Bitbucket, Reddit, and web sources.")
    readme_content.append("")
    readme_content.append("📊 [View Historical Data](./data/)")
    readme_content.append("")

    # Established Addons section
    readme_content.append("## 🏆 Established Addons")
    readme_content.append("")
    if established:
        table = _create_tier_table(established, 'established')
        readme_content.extend(table)
    else:
        readme_content.append("*No established addons found this week.*")
    readme_content.append("")

    # Rising Addons section
    readme_content.append("## 📈 Rising Addons")
    readme_content.append("")
    if rising:
        table = _create_tier_table(rising, 'rising')
        readme_content.extend(table)
    else:
        readme_content.append("*No rising addons found this week.*")
    readme_content.append("")

    # New Addons section
    readme_content.append("## 🆕 New Addons")
    readme_content.append("")
    if new:
        table = _create_tier_table(new, 'new')
        readme_content.extend(table)
    else:
        readme_content.append("*No new addons found this week.*")
    readme_content.append("")

    # Footer
    readme_content.append("---")
    readme_content.append("")
    readme_content.append("*This list is automatically generated every Friday. Data sources include GitHub, GitLab, Reddit (r/kodi, r/Addons4Kodi), and various RSS feeds.*")
    readme_content.append("")

    # Write to README.md
    readme_path = Path(REPO_ROOT) / "README.md"

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(readme_content))

        logger.info(f"README.md generated successfully: {readme_path}")

    except Exception as e:
        logger.error(f"Error generating README.md: {e}")
        raise


def _create_tier_table(repos, tier_type):
    """
    Create markdown table for a tier.

    Args:
        repos: List of repositories in this tier
        tier_type: Type of tier ('established', 'rising', 'new')

    Returns:
        list: Lines of markdown table
    """
    table = []

    # Table header - different for rising tier
    if tier_type == 'rising':
        table.append("| Rank | Repository | Developer | Maintainers | Stars | Last Activity | Growth Signal |")
        table.append("|------|------------|-----------|-------------|-------|---------------|---------------|")
    else:
        table.append("| Rank | Repository | Developer | Maintainers | Stars | Last Activity | Description |")
        table.append("|------|------------|-----------|-------------|-------|---------------|-------------|")

    # Table rows
    for repo in repos:
        rank = f"#{repo.get('rank_in_tier', 0)}"
        repo_name = repo.get('name', 'Unknown')
        repo_url = repo.get('repo_url', '#')
        repo_link = f"[{repo_name}]({repo_url})"

        developer = repo.get('owner', 'Unknown')

        # Maintainers - up to 3
        contributors = repo.get('contributors', [])
        if contributors:
            maintainers = ', '.join(contributors[:3])
        else:
            maintainers = developer

        # Stars with emoji
        stars = repo.get('stars', 0)
        stars_str = f"⭐ {stars:,}"

        # Last activity (human-readable)
        last_activity_date = repo.get('last_activity_date') or repo.get('last_commit_date')
        last_activity = format_time_ago(last_activity_date) if last_activity_date else "Unknown"

        # Last column varies by tier
        if tier_type == 'rising':
            # Growth signal for rising tier
            growth_signals = []

            star_velocity = repo.get('star_velocity_30d', 0)
            if star_velocity > 0:
                growth_signals.append(f"+{star_velocity} stars (30d)")

            recent_mentions = repo.get('recent_mentions_30d', 0)
            if recent_mentions > 0:
                growth_signals.append(f"{recent_mentions} Reddit mentions")

            web_mentions = repo.get('web_mentions', 0)
            if web_mentions > 0:
                growth_signals.append(f"{web_mentions} web mentions")

            if not growth_signals:
                growth_signals.append("Active development")

            last_col = ', '.join(growth_signals[:2])  # Show top 2 signals
        else:
            # Description for established and new tiers
            description = repo.get('description', '')
            # Truncate long descriptions
            if len(description) > 100:
                description = description[:97] + "..."
            last_col = description if description else "No description"

        # Build row (escape pipe characters in descriptions)
        last_col = last_col.replace('|', '\\|')
        maintainers = maintainers.replace('|', '\\|')

        row = f"| {rank} | {repo_link} | {developer} | {maintainers} | {stars_str} | {last_activity} | {last_col} |"
        table.append(row)

    return table
