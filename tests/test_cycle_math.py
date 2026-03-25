"""Tests for cycle_math."""
import pytest
from datetime import date

from custom_components.cyclist.cycle_math import (
    calculate_cycle_day,
    is_period_active,
    calculate_next_period_date,
    calculate_days_until_next_period,
    calculate_fertility_window,
    get_fertility,
    get_phase,
    detect_bbt_shift,
    detect_cm_peak,
    detect_lh_peak,
    get_ovulation_confirmation,
)
from custom_components.cyclist.const import (
    PHASE_MENSTRUATION,
    PHASE_FOLLICULAR,
    PHASE_OVULATION,
    PHASE_LUTEAL,
    FERTILITY_FERTILE,
    FERTILITY_LOW,
    FERTILITY_SAFER,
    CM_DRY,
    CM_STICKY,
    CM_CREAMY,
    CM_WATERY,
    CM_EGGWHITE,
    LH_NEGATIVE,
    LH_POSITIVE,
    LH_PEAK,
    ATTR_BBT,
    ATTR_CM,
    ATTR_LH,
)

def test_calculate_cycle_day():
    last_start = date(2026, 3, 1)
    # Day 1
    assert calculate_cycle_day(date(2026, 3, 1), last_start) == 1
    # Day 14
    assert calculate_cycle_day(date(2026, 3, 14), last_start) == 14
    # Day 28
    assert calculate_cycle_day(date(2026, 3, 28), last_start) == 28

def test_is_period_active():
    assert is_period_active(1, 5) is True
    assert is_period_active(5, 5) is True
    assert is_period_active(6, 5) is False

def test_calculate_next_period_date():
    last_start = date(2026, 3, 1)
    assert calculate_next_period_date(last_start, 28) == date(2026, 3, 29)

def test_calculate_days_until_next_period():
    last_start = date(2026, 3, 1)
    # Today is Mar 15, next is Mar 29 (14 days)
    assert calculate_days_until_next_period(date(2026, 3, 15), last_start, 28) == 14

def test_get_fertility():
    # 28 day cycle
    # fw = 10 to 17
    # low = 8, 9, 18, 19
    assert get_fertility(1, 28) == FERTILITY_SAFER
    assert get_fertility(7, 28) == FERTILITY_SAFER
    assert get_fertility(8, 28) == FERTILITY_LOW
    assert get_fertility(10, 28) == FERTILITY_FERTILE
    assert get_fertility(14, 28) == FERTILITY_FERTILE
    assert get_fertility(17, 28) == FERTILITY_FERTILE
    assert get_fertility(19, 28) == FERTILITY_LOW
    assert get_fertility(20, 28) == FERTILITY_SAFER

def test_get_phase():
    # 28 cycle, 5 period
    # men: 1-5
    # fol: 6-11
    # ovu: 12-16 (center 14 +/- 2)
    # lut: 17-28
    assert get_phase(1, 28, 5) == PHASE_MENSTRUATION
    assert get_phase(5, 28, 5) == PHASE_MENSTRUATION
    assert get_phase(6, 28, 5) == PHASE_FOLLICULAR
    assert get_phase(11, 28, 5) == PHASE_FOLLICULAR
    assert get_phase(12, 28, 5) == PHASE_OVULATION
    assert get_phase(14, 28, 5) == PHASE_OVULATION
    assert get_phase(16, 28, 5) == PHASE_OVULATION
    assert get_phase(17, 28, 5) == PHASE_LUTEAL
    assert get_phase(28, 28, 5) == PHASE_LUTEAL

def test_short_cycle():
    # 21 day cycle, 3 period
    # fw = 3 to 10
    # center = 7 +/- 2 = 5 to 9
    assert get_phase(1, 21, 3) == PHASE_MENSTRUATION
    assert get_phase(4, 21, 3) == PHASE_FOLLICULAR
    assert get_phase(5, 21, 3) == PHASE_OVULATION
    assert get_phase(9, 21, 3) == PHASE_OVULATION
    assert get_phase(10, 21, 3) == PHASE_LUTEAL
    
    assert get_fertility(3, 21) == FERTILITY_FERTILE
    assert get_fertility(1, 21) == FERTILITY_LOW # 3-2 = 1
    assert get_fertility(11, 21) == FERTILITY_LOW # 10+1 = 11

def test_long_cycle():
    # 35 cycle, 7 period
    # fw = 17 to 24
    # center = 21 +/- 2 = 19 to 23
    assert get_phase(7, 35, 7) == PHASE_MENSTRUATION
    assert get_phase(18, 35, 7) == PHASE_FOLLICULAR
    assert get_phase(21, 35, 7) == PHASE_OVULATION
    assert get_phase(24, 35, 7) == PHASE_LUTEAL

def test_edge_cases():
    # day > cycle_length
    assert get_phase(30, 28, 5) == PHASE_LUTEAL

def test_detect_bbt_shift():
    # Baseline 6 days: 97.0
    # Shift 3 days: 97.2 (delta 0.2)
    temps = [97.0] * 6 + [97.2] * 3
    assert detect_bbt_shift(temps) == 6
    
    # Not enough days
    assert detect_bbt_shift([97.0] * 5 + [97.2] * 3) is None
    
    # Not high enough
    temps = [97.0] * 6 + [97.05] * 3
    assert detect_bbt_shift(temps) is None
    
    # High but not consecutive
    temps = [97.0] * 6 + [97.2, 97.0, 97.2]
    assert detect_bbt_shift(temps) is None

def test_detect_cm_peak():
    mucus = [CM_DRY, CM_STICKY, CM_WATERY, CM_EGGWHITE, CM_DRY]
    # Last day of fertile mucus is index 3
    assert detect_cm_peak(mucus) == 3
    
    mucus = [CM_DRY, CM_WATERY, CM_WATERY, CM_STICKY]
    assert detect_cm_peak(mucus) == 2

def test_detect_lh_peak():
    lh = [LH_NEGATIVE, LH_NEGATIVE, LH_POSITIVE, LH_PEAK, LH_NEGATIVE]
    # First positive result is index 2
    assert detect_lh_peak(lh) == 2

def test_get_ovulation_confirmation():
    last_start = date(2026, 3, 1)
    # Day 1-6: 97.0, CM dry
    # Day 7: LH positive, CM egg_white
    # Day 8: CM sticky
    # Day 9-11: 97.2 (BBT shift)
    daily_logs = {
        "2026-03-01": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-02": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-03": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-04": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-05": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-06": {ATTR_BBT: 97.0, ATTR_CM: CM_DRY},
        "2026-03-07": {ATTR_CM: CM_EGGWHITE, ATTR_LH: LH_POSITIVE},
        "2026-03-08": {ATTR_CM: CM_STICKY},
        "2026-03-09": {ATTR_BBT: 97.2},
        "2026-03-10": {ATTR_BBT: 97.2},
        "2026-03-11": {ATTR_BBT: 97.2},
    }
    
    conf = get_ovulation_confirmation(last_start, daily_logs, 28)
    # BBT shift started on Day 9 (index 8)
    assert conf["confirmed_day"] == 9
    # CM peak was Day 7 (index 6)
    assert conf["peak_day"] == 7
    assert set(conf["methods"]) == {"bbt", "cm", "lh"}

def test_advanced_fertility():
    last_start = date(2026, 3, 1)
    daily_logs = {
        "2026-03-07": {ATTR_CM: CM_EGGWHITE}, # Day 7
    }
    
    # Calendar would say day 7 is SAFER (fw starts day 10)
    # But symptom says FERTILE
    assert get_fertility(7, 28, last_start, daily_logs) == FERTILITY_FERTILE
    
    # After shift confirmed (Day 9)
    daily_logs.update({
        "2026-03-01": {ATTR_BBT: 97.0},
        "2026-03-02": {ATTR_BBT: 97.0},
        "2026-03-03": {ATTR_BBT: 97.0},
        "2026-03-04": {ATTR_BBT: 97.0},
        "2026-03-05": {ATTR_BBT: 97.0},
        "2026-03-06": {ATTR_BBT: 97.0},
        "2026-03-09": {ATTR_BBT: 97.2},
        "2026-03-10": {ATTR_BBT: 97.2},
        "2026-03-11": {ATTR_BBT: 97.2},
    })
    # Day 12 is 3 days after shift start (Day 9) -> SAFER
    assert get_fertility(12, 28, last_start, daily_logs) == FERTILITY_SAFER
