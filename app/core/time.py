from datetime import datetime, timezone


def utc_now() -> datetime:
    """返回带 UTC 时区信息的当前时间。"""
    return datetime.now(timezone.utc)
