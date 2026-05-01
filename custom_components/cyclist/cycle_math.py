"""Core cycle math logic."""
from datetime import date, timedelta

from .const import (
    PHASE_MENSTRUATION,
    PHASE_FOLLICULAR,
    PHASE_OVULATION,
    PHASE_LUTEAL,
    PHASE_LATE,
    FERTILITY_FERTILE,
    FERTILITY_LOW,
    FERTILITY_SAFER,
    GOAL_AVOID,
    GOAL_PLAN,
    CM_WATERY,
    CM_EGGWHITE,
    LH_POSITIVE,
    LH_PEAK,
    ATTR_BBT,
    ATTR_CM,
    ATTR_LH,
)

def calculate_cycle_day(today: date, last_period_start: date) -> int:
    """Calculate current day in cycle (1-based)."""
    return (today - last_period_start).days + 1

def is_period_active(cycle_day: int, period_duration: int) -> bool:
    """Check if period is ongoing."""
    return cycle_day <= period_duration

def calculate_next_period_date(last_period_start: date, cycle_length: int, offset: int = 0) -> date:
    """Calculate date of next predicted period."""
    return last_period_start + timedelta(days=cycle_length + offset)

def calculate_days_until_next_period(today: date, last_period_start: date, cycle_length: int, offset: int = 0) -> int:
    """Calculate days remaining until next period."""
    next_date = calculate_next_period_date(last_period_start, cycle_length, offset)
    return (next_date - today).days

def calculate_fertility_window(cycle_length: int) -> tuple[int, int]:
    """Calculate start and end days of fertile window."""
    fertile_window_start = cycle_length - 18
    fertile_window_end = cycle_length - 11
    return fertile_window_start, fertile_window_end

def get_calendar_fertility(cycle_day: int, cycle_length: int) -> str:
    """Get fertility status for a given day using the calendar method."""
    fertile_window_start, fertile_window_end = calculate_fertility_window(cycle_length)
    low_zone_start = fertile_window_start - 2
    low_zone_end = fertile_window_end + 2
    
    if low_zone_start <= cycle_day <= low_zone_end:
        if fertile_window_start <= cycle_day <= fertile_window_end:
            return FERTILITY_FERTILE
        return FERTILITY_LOW
    return FERTILITY_SAFER

def get_fertility(
    cycle_day: int, 
    cycle_length: int, 
    last_period_start: date | None = None, 
    daily_logs: dict[str, dict[str, Any]] | None = None
) -> str:
    """Get fertility status, prioritizing symptoms (CM, LH) over calendar if available."""
    if last_period_start is None or daily_logs is None:
        return get_calendar_fertility(cycle_day, cycle_length)
        
    data = get_cycle_data(last_period_start, daily_logs, cycle_length)
    idx = cycle_day - 1
    
    # If we have egg-white or watery mucus, it's PEAK fertility
    if idx < len(data[ATTR_CM]):
        mucus = data[ATTR_CM][idx]
        if mucus in {CM_WATERY, CM_EGGWHITE}:
            return FERTILITY_FERTILE
            
    # If LH is positive or peak, it's PEAK fertility
    if idx < len(data[ATTR_LH]):
        lh = data[ATTR_LH][idx]
        if lh in {LH_POSITIVE, LH_PEAK}:
            return FERTILITY_FERTILE
            
    # Check if ovulation is already confirmed
    conf = get_ovulation_confirmation(last_period_start, daily_logs, cycle_length)
    if conf["confirmed_day"] and cycle_day >= conf["confirmed_day"] + 3:
        # 3 days after BBT shift, fertility is SAFER
        return FERTILITY_SAFER
        
    # Fallback to calendar
    return get_calendar_fertility(cycle_day, cycle_length)

def get_fertility_status(
    cycle_day: int, 
    cycle_length: int, 
    goal: str,
    last_period_start: date | None = None,
    daily_logs: dict[str, dict[str, Any]] | None = None
) -> str:
    """Get actionable status based on goal and fertility level."""
    fertility = get_fertility(cycle_day, cycle_length, last_period_start, daily_logs)
    
    if goal == GOAL_AVOID:
        if fertility == FERTILITY_FERTILE:
            return "high_chance"
        if fertility == FERTILITY_LOW:
            return "caution"
        return "low_chance"
        
    if goal == GOAL_PLAN:
        if fertility == FERTILITY_FERTILE:
            return "peak_fertility"
        if fertility == FERTILITY_LOW:
            return "fertility_rising"
        return "low_fertility"
        
    return fertility # Default to basic fertility labels for "track"

def get_phase(cycle_day: int, cycle_length: int, period_duration: int) -> str:
    """Get cycle phase for a given day."""
    if cycle_day > cycle_length:
        return PHASE_LATE
        
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

def detect_bbt_shift(temperatures: list[float]) -> int | None:
    """
    Detect BBT shift using the 3/6 rule.
    Returns the index (0-based) of the FIRST day of the shift if confirmed.
    3 consecutive temperatures must be higher than the average of the previous 6.
    """
    if len(temperatures) < 9:
        return None

    # We need at least 3 consecutive shift days
    for i in range(len(temperatures) - 2):
        shift = temperatures[i:i+3]
        # Shift days must be consecutive and non-None
        if any(t is None for t in shift):
            continue
            
        # Look back for 6 baseline days (not necessarily immediate indices)
        baseline = []
        for j in range(i - 1, -1, -1):
            if temperatures[j] is not None:
                baseline.append(temperatures[j])
            if len(baseline) == 6:
                break
        
        if len(baseline) < 6:
            continue
            
        avg_baseline = sum(baseline) / 6
        # Shift must be higher than the baseline average
        if all(t > avg_baseline + 0.1 for t in shift):
            return i
            
    return None

def detect_cm_peak(mucus_types: list[str]) -> int | None:
    """
    Detect the CM Peak Day (the LAST day of fertile mucus).
    Returns the index (0-based) of the peak day.
    """
    fertile_types = {CM_WATERY, CM_EGGWHITE}
    peak_day = None
    
    for i, m_type in enumerate(mucus_types):
        if m_type in fertile_types:
            peak_day = i
        elif peak_day is not None and m_type is not None:
            # If we found a peak and then found a non-fertile type, 
            # the previous peak day remains the peak.
            # But we only confirm it if we have at least 3 days of drying up.
            # For simplicity, we just return the last known fertile day for now.
            pass
            
    return peak_day

def detect_lh_peak(lh_results: list[str]) -> int | None:
    """
    Detect the LH Peak (the FIRST day of a positive/peak result).
    Returns the index (0-based) of the first positive result.
    """
    positive_results = {LH_POSITIVE, LH_PEAK}
    for i, result in enumerate(lh_results):
        if result in positive_results:
            return i
    return None

def get_cycle_data(last_period_start: date, daily_logs: dict[str, dict[str, Any]], cycle_length: int) -> dict[str, list]:
    """
    Convert daily_logs into lists of data points for the current cycle.
    Each list will be indexed by cycle day (0-based, where 0 is Day 1).
    """
    bbt_list = [None] * (cycle_length + 14) # Allow some overflow
    cm_list = [None] * (cycle_length + 14)
    lh_list = [None] * (cycle_length + 14)
    
    for date_str, data in daily_logs.items():
        log_date = date.fromisoformat(date_str)
        cycle_day = calculate_cycle_day(log_date, last_period_start)
        
        # We only care about logs from the current cycle (Day 1+)
        if 1 <= cycle_day <= len(bbt_list):
            idx = cycle_day - 1
            bbt_list[idx] = data.get(ATTR_BBT)
            cm_list[idx] = data.get(ATTR_CM)
            lh_list[idx] = data.get(ATTR_LH)
            
    return {
        ATTR_BBT: bbt_list,
        ATTR_CM: cm_list,
        ATTR_LH: lh_list,
    }

def get_ovulation_confirmation(last_period_start: date, daily_logs: dict[str, dict[str, Any]], cycle_length: int) -> dict[str, Any]:
    """
    Check for confirmed ovulation using all available data.
    Returns a dict with confirmed_day, peak_day, and methods used.
    """
    data = get_cycle_data(last_period_start, daily_logs, cycle_length)
    
    bbt_shift_idx = detect_bbt_shift(data[ATTR_BBT])
    cm_peak_idx = detect_cm_peak(data[ATTR_CM])
    lh_peak_idx = detect_lh_peak(data[ATTR_LH])
    
    confirmed_day = None
    peak_day = None
    methods = []
    
    # Ovulation typically occurs 1 day BEFORE the BBT shift
    if bbt_shift_idx is not None:
        confirmed_day = bbt_shift_idx # Day of shift (Day 1 of high temp)
        methods.append("bbt")
        
    # Peak day is the last day of fertile mucus
    if cm_peak_idx is not None:
        peak_day = cm_peak_idx + 1 # Convert to 1-based cycle day
        methods.append("cm")
        
    if lh_peak_idx is not None:
        # LH peak usually occurs 24-48h before ovulation
        # We don't use it to confirm post-ovulation, but to identify the window
        methods.append("lh")
        
    return {
        "confirmed_day": confirmed_day + 1 if confirmed_day is not None else None,
        "peak_day": peak_day,
        "methods": methods
    }
