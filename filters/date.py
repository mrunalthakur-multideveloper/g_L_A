"""
Date Filter Module
Filters jobs by publication date (TARGET_DATE, last 24 hours, or all) without altering original date_posted values.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


def parse_date_to_iso(date_val: Union[str, int, float, None]) -> Optional[datetime]:
    """Parses various date formats to timezone-naive UTC datetime object"""
    if not date_val:
        return None
    try:
        if isinstance(date_val, (int, float)):
            # Timestamp (ms or s)
            ts = date_val / 1000.0 if date_val > 1e11 else float(date_val)
            return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
            
        if isinstance(date_val, str):
            val = date_val.strip()
            # Handle standard ISO formats, Z, and offsets
            val_clean = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(val_clean)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
    except Exception:
        pass
    return None


def matches_date_filter(
    date_val: Union[str, int, float, None],
    target_date: Optional[str] = None,
    last_24_hours: bool = False,
    hours_window: Optional[int] = None
) -> bool:
    """
    Checks if job publication date satisfies target date, last 24h, or hours_window filter.
    If target_date is given (YYYY-MM-DD), checks for matching day.
    If hours_window is given, checks within past N hours (UTC).
    If last_24_hours is True, checks within past 24 hours (UTC).
    If neither is configured, returns True.
    """
    # Environment variable check if not provided explicitly
    if target_date is None:
        target_date = os.getenv("TARGET_DATE")
        
    if not target_date and not last_24_hours and not hours_window:
        return True
        
    dt = parse_date_to_iso(date_val)
    if not dt:
        # Strictly exclude jobs with missing or unparseable dates when filtering
        return False
        
    if target_date:
        job_day = dt.strftime("%Y-%m-%d")
        return job_day == target_date.strip()
        
    effective_hours = hours_window if hours_window is not None else (24 if last_24_hours else None)
    if effective_hours is not None:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=effective_hours)
        return dt >= cutoff
        
    return True

