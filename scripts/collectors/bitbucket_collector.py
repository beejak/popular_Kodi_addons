"""Bitbucket repository data collector (stub for POC)."""

from scripts.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_bitbucket_repos():
    """
    Collect repository data from Bitbucket API.

    Note: This is a stub implementation for POC phase.
    Bitbucket has limited search API capabilities and is lower priority.
    Can be implemented in Phase 2 if needed.

    Returns:
        list: Empty list (Bitbucket collection not yet implemented)
    """
    logger.info("Bitbucket collector called (stub implementation - skipping)")
    return []
