import logging


def configure_logging() -> None:
    """Send joblens.* INFO logs to stderr.

    Uvicorn only configures its own loggers, so without this our INFO lines
    would be dropped. Configures the package logger, not root, so httpx and
    anthropic stay quiet; propagation stays on so pytest's caplog sees records.
    """
    logger = logging.getLogger("joblens")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:  %(name)s  %(message)s"))
        logger.addHandler(handler)
