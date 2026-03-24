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
)
from custom_components.cyclist.const import (
    PHASE_MENSTRUATION,
    PHASE_FOLLICULAR,
    PHASE_OVULATION,
    PHASE_LUTEAL,
    FERTILITY_FERTILE,
    FERTILITY_LOW,
    FERTILITY_SAFER,
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
