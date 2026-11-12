import logging
from pathlib import Path


def setup_logger(name: str, log_dir: str, level: str = "INFO") -> logging.Logger:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    level_value = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level_value)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(stream_handler)
        logger.propagate = False

    file_logger = logging.getLogger(f"{name}.file")
    if not file_logger.handlers:
        file_logger.setLevel(level_value)
        file_handler = logging.FileHandler(log_path / "api_test.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        file_logger.addHandler(file_handler)
        file_logger.propagate = False

    logger.file = file_logger  # type: ignore[attr-defined]
    return logger
