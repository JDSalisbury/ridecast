import logging
import sys
from pathlib import Path


def log_fun_fact(fun_fact: str, user_name: str) -> None:
    """save fun fact to text file."""
    script_dir = Path(__file__).resolve().parent
    file_path = script_dir / "fun_facts.txt"

    with open(file_path, "a") as f:
        f.write(f"Fun Fact for {user_name}: {fun_fact}\n")


def load_fun_facts(user) -> list[str]:
    """Load fun facts from text file."""
    script_dir = Path(__file__).resolve().parent
    file_path = script_dir / "fun_facts.txt"

    if not file_path.exists():
        return []

    with open(file_path, "r") as f:
        return [line for line in f.readlines() if user in line]


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
