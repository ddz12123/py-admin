import logging
import sys

LOGGER_NAME = "py-admin"


def setup_logging(level: str = "INFO", *, disable_uvicorn_access_log: bool = True) -> None:
    """配置应用日志；重复创建应用时不会叠加 Handler。"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    app_logger = logging.getLogger(LOGGER_NAME)
    app_logger.setLevel(log_level)
    app_logger.propagate = False
    for handler in app_logger.handlers:
        handler.close()
    app_logger.handlers.clear()
    app_logger.addHandler(console_handler)

    # 使用自定义访问日志时关闭 Uvicorn 的重复访问日志；关闭自定义日志时恢复它。
    logging.getLogger("uvicorn.access").disabled = disable_uvicorn_access_log
    logging.captureWarnings(True)


logger = logging.getLogger(LOGGER_NAME)
