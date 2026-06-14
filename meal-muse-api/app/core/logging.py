"""日志系统配置"""

import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logging():
    """初始化日志系统"""
    level = logging.DEBUG if settings.ENV == "dev" else logging.INFO
    format_str = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.ENV == "dev"
        else '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_str))
    handler.setLevel(level)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # 降低第三方库日志级别
    for name in ["uvicorn", "sqlalchemy.engine", "httpcore", "httpx"]:
        logging.getLogger(name).setLevel(logging.WARNING)

    # 项目日志
    logging.getLogger("meal_muse").setLevel(level)
