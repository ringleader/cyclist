"""Core cycle math logic."""
from datetime import date, timedelta

from .const import (
    PHASE_MENSTRUATION,
    PHASE_FOLLICULAR,
    PHASE_OVULATION,
    PHASE_LUTEAL,
    FERTILITY_FERTILE,
    FERTILITY_LOW,
    FERTILITY_SAFER,
)

def calculate_cycle_day(today: date, last_period_start: date) -> int:
    """Calculate current day in cycle (1-based)."""
    return (today - last_period_start).days + 1

def is_period_active(cycle_day: int, period_duration: int) -> bool:
    """Check if period is ongoing."""
    return cycle_day <= period_duration

def calculate_next_period_date(last_period_start: date, cycle_length: int) -> date:
    """Calculate date of next predicted period."""
    return last_period_start + timedelta(days=cycle_length)

def calculate_days_until_next_period(today: date, last_period_start: date, cycle_length: int) -> int:
    """Calculate days remaining until next period."""
    next_date = calculate_next_period_date(last_period_start, cycle_length)
    return (next_date - today).days

def calculate_fertility_window(cycle_length: int) -> tuple[int, int]:
    """Calculate start and end days of fertile window."""
    fertile_window_start = cycle_length - 18
    fertile_window_end = cycle_length - 11
    return fertile_window_start, fertile_window_end

def get_fertility(cycle_day: int, cycle_length: int) -> str:
    """Get fertility status for a given day."""
    fertile_window_start, fertile_window_end = calculate_fertility_window(cycle_length)
    low_zone_start = fertile_window_start - 2
    low_zone_end = fertile_window_end + 2
    
    if low_zone_start <= cycle_day <= low_zone_end:
        if fertile_window_start <= cycle_day <= fertile_window_end:
            return FERTILITY_FERTILE
        return FERTILITY_LOW
    return FERTILITY_SAFER

def get_phase(cycle_day: int, cycle_length: int, period_duration: int) -> str:
    """Get cycle phase for a given day."""
    if cycle_day <= period_duration:
        return PHASE_MENSTRUATION
        
    ovulation_estimate = cycle_length - 14
    ovulation_start = ovulation_estimate - 2
    ovulation_end = ovulation_estimate + 2
    
    if cycle_day < ovulation_start:
        return PHASE_FOLLICULAR
    elif cycle_day <= ovulation_end:
        return PHASE_OVULATION
    else:
        return PHASE_LUTEAL
