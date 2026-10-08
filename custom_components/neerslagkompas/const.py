"""Integration configuration and source definitions."""
from datetime import timedelta

DOMAIN = "neerslagkompas"
CONF_TRACK_HOME = "track_home"
CONF_KNMI_KEY = "knmi_key"
CONF_WEERLIVE_KEY = "weerlive_key"
CONF_BUIENALARM = "buienalarm_enabled"
CONF_BUIENRADAR = "buienradar_enabled"
SOURCE_INTERVALS = {
    "buienalarm": timedelta(minutes=5),
    "buienradar": timedelta(minutes=5),
    "knmi_radar": timedelta(minutes=15),
    "weerlive": timedelta(minutes=30),
}
