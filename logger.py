import logging
import sys
from pathlib import Path
from fun_facts_db import FunFactsDB


# Global fun facts database instance
_fun_facts_db = None


def get_fun_facts_db() -> FunFactsDB:
    """Get singleton instance of fun facts database."""
    global _fun_facts_db
    if _fun_facts_db is None:
        _fun_facts_db = FunFactsDB()
    return _fun_facts_db


def log_fun_fact(fun_fact: str, user_name: str, category: str = "general") -> bool:
    """Save fun fact to database. Returns True if added, False if duplicate."""
    db = get_fun_facts_db()
    return db.add_fun_fact(fun_fact, user_name, category)


def load_fun_facts(user_name: str) -> str:
    """Load fun facts summary for context (not full facts to avoid repetition)."""
    db = get_fun_facts_db()
    return db.get_recent_facts_summary(user_name)


def get_suggested_category(user_name: str) -> str:
    """Get a suggested category that hasn't been used recently."""
    db = get_fun_facts_db()
    return db.get_unused_category(user_name)


def cleanup_old_fun_facts(days_to_keep: int = 90) -> int:
    """Clean up old fun facts. Returns count of removed facts."""
    db = get_fun_facts_db()
    return db.cleanup_old_facts(days_to_keep)


def get_fun_facts_stats(user_name: str) -> dict:
    """Get statistics about user's fun facts."""
    db = get_fun_facts_db()
    return db.get_stats(user_name)


def setup_logger(name: str = "ridecast", log_level: str = "INFO") -> logging.Logger:
    """Setup and configure logger for the application."""

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    console_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)

    return logger


# Default logger instance
logger = setup_logger()
