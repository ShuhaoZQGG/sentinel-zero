"""Time parsing utilities for handling various time formats."""

import re
from typing import Union


def parse_time_to_seconds(time_str: Union[str, int, float]) -> float:
    """Parse time string to seconds.
    
    Supports formats:
    - Plain numbers: "60" -> 60 seconds
    - Seconds: "45s" -> 45 seconds
    - Minutes: "30m" -> 1800 seconds
    - Hours: "5h" -> 18000 seconds
    - Days: "2d" -> 172800 seconds
    - Combined: "1h30m" -> 5400 seconds
    - Combined: "2d4h30m15s" -> 189015 seconds
    
    Args:
        time_str: Time string or number
        
    Returns:
        Time in seconds as float
        
    Raises:
        ValueError: If time format is invalid
    """
    if isinstance(time_str, (int, float)):
        return float(time_str)
    
    time_str = str(time_str).strip()
    
    # If it's a plain number, return it as seconds
    try:
        return float(time_str)
    except ValueError:
        pass
    
    # Parse time format with units
    total_seconds = 0.0
    
    # Pattern to match time components
    pattern = r'(\d+(?:\.\d+)?)\s*([dhms])'
    matches = re.findall(pattern, time_str.lower())
    
    if not matches:
        raise ValueError(f"Invalid time format: {time_str}")
    
    units = {
        'd': 86400,  # days
        'h': 3600,   # hours
        'm': 60,     # minutes
        's': 1       # seconds
    }
    
    for value, unit in matches:
        if unit not in units:
            raise ValueError(f"Invalid time unit: {unit}")
        total_seconds += float(value) * units[unit]
    
    return total_seconds


def format_seconds_to_human(seconds: float) -> str:
    """Format seconds to human-readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Human-readable time string (e.g., "2h30m", "5m15s")
    """
    if seconds < 1:
        return f"{seconds:.1f}s"
    
    parts = []
    
    # Days
    if seconds >= 86400:
        days = int(seconds // 86400)
        parts.append(f"{days}d")
        seconds %= 86400
    
    # Hours
    if seconds >= 3600:
        hours = int(seconds // 3600)
        parts.append(f"{hours}h")
        seconds %= 3600
    
    # Minutes
    if seconds >= 60:
        minutes = int(seconds // 60)
        parts.append(f"{minutes}m")
        seconds %= 60
    
    # Seconds
    if seconds > 0 or not parts:
        if seconds == int(seconds):
            parts.append(f"{int(seconds)}s")
        else:
            parts.append(f"{seconds:.1f}s")
    
    return ''.join(parts)