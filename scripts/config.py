"""Configuration constants for Kodi Repository Discovery & Tracking Tool."""

import os

# Minimum thresholds
MIN_STARS = 20
ACTIVITY_MONTHS = 6

# POC mode - limit to 10 repositories total for testing
POC_MODE = os.getenv('POC_MODE', 'false').lower() == 'true'
POC_LIMIT = 10

# Tier age thresholds (in days)
TIER_AGE_THRESHOLDS = {
    'new': 90,        # < 3 months
    'rising': 365,    # 3-12 months
    'established': float('inf')  # 12+ months
}

# Search keywords for Kodi repositories
SEARCH_KEYWORDS = [
    "kodi addon",
    "kodi plugin",
    "kodi repository",
    "xbmc addon",
    "xbmc plugin",
    "kodi script",
    "kodi skin",
    "kodi service"
]

# RSS Feeds to monitor for web mentions
RSS_FEEDS = [
    "https://kodi.tv/rss.xml",  # Official Kodi blog
    # Additional feeds can be added here
]

# Subreddits to monitor for social signals
SUBREDDITS = [
    "kodi",
    "Addons4Kodi",
    "selfhosted",
    "cordcutters"
]

# API timeouts (seconds)
API_TIMEOUT = 30

# Ranking weights for established tier
ESTABLISHED_WEIGHTS = {
    'stars': 0.6,
    'recent_activity': 0.2,
    'social_signals': 0.2
}

# Ranking weights for rising tier
RISING_WEIGHTS = {
    'growth_rate': 0.4,
    'stars': 0.3,
    'recent_activity': 0.2,
    'social_signals': 0.1
}

# Ranking weights for new tier
NEW_WEIGHTS = {
    'recent_activity': 0.5,
    'stars': 0.3,
    'social_signals': 0.2
}

# Growth signal thresholds for rising tier
GROWTH_THRESHOLDS = {
    'star_velocity_per_month': 10,  # Stars gained per month
    'commit_increase_ratio': 1.2,   # Recent commits vs older commits ratio
}

# Data directory paths (relative to repository root)
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
CURRENT_DIR = os.path.join(DATA_DIR, "current")

# Repository root (parent of scripts directory)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
