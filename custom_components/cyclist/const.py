"""Constants for the Cyclist integration."""

DOMAIN = "cyclist"
CONF_NAME = "name"
STORAGE_KEY = "cyclist.storage"
STORAGE_VERSION = 1

CONF_CYCLE_LENGTH = "cycle_length"
CONF_PERIOD_DURATION = "period_duration"
CONF_LAST_PERIOD_START = "last_period_start"
CONF_GOAL = "goal"

GOAL_AVOID = "avoid"
GOAL_PLAN = "plan"
GOAL_TRACK = "track"

DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_DURATION = 5
DEFAULT_GOAL = GOAL_TRACK

PHASE_MENSTRUATION = "menstruation"
PHASE_FOLLICULAR = "follicular"
PHASE_OVULATION = "ovulation"
PHASE_LUTEAL = "luteal"
PHASE_LATE = "late"

FERTILITY_FERTILE = "fertile"
FERTILITY_LOW = "low"
FERTILITY_SAFER = "safer"

ATTR_LAST_PERIOD_START = "last_period_start"

SYMPTOMS = ["cramps", "headache", "low_energy", "mood_change"]

# Advanced tracking constants
ATTR_BBT = "bbt"
ATTR_CM = "cm"
ATTR_LH = "lh"

CM_DRY = "dry"
CM_STICKY = "sticky"
CM_CREAMY = "creamy"
CM_WATERY = "watery"
CM_EGGWHITE = "egg_white"

LH_NEGATIVE = "negative"
LH_POSITIVE = "positive"
LH_PEAK = "peak"

CM_TYPES = [CM_DRY, CM_STICKY, CM_CREAMY, CM_WATERY, CM_EGGWHITE]
LH_RESULTS = [LH_NEGATIVE, LH_POSITIVE, LH_PEAK]

# Fertility window types
WINDOW_CALENDAR = "calendar"
WINDOW_SYMPTOTHERMAL = "symptothermal"
