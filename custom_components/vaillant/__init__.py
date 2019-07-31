"""
Vaillant base component.
"""
import logging
from datetime import timedelta
from urllib.error import HTTPError

import voluptuous as vol

from homeassistant.const import (
    CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME, CONF_DISCOVERY)
    
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

from .const import DATA_VAILLANT_AUTH

REQUIREMENTS = [
    'https://github.com/pjmaenh/pyvaillant/archive/'
    'v0.0.4.zip#pyvaillant==0.0.4']

_LOGGER = logging.getLogger(__name__)

CONF_SECRET_KEY = 'secret_key'
CONF_USER_PREFIX = 'user_prefix'
CONF_APP_VERSION = 'app_version'

DOMAIN = 'vaillant'

DEFAULT_DISCOVERY = True

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=10)
MIN_TIME_BETWEEN_EVENT_UPDATES = timedelta(seconds=10)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_SECRET_KEY): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Optional(CONF_DISCOVERY, default=DEFAULT_DISCOVERY): cv.boolean,
        vol.Required(CONF_APP_VERSION): cv.string,
        vol.Required(CONF_USER_PREFIX): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    import pyvaillant


    try:
        auth = pyvaillant.ClientAuth(
            config[DOMAIN][CONF_API_KEY], config[DOMAIN][CONF_SECRET_KEY],
            config[DOMAIN][CONF_USERNAME], config[DOMAIN][CONF_PASSWORD],
            'read_station read_camera access_camera '
            'read_thermostat write_thermostat '
            'read_presence access_presence',
            config[DOMAIN][CONF_APP_VERSION], config[DOMAIN][CONF_USER_PREFIX])

    except HTTPError:
        _LOGGER.error("Unable to connect to Vaillant API")
        return False

    # Store config to be used during entry setup
    hass.data[DATA_VAILLANT_AUTH] = auth

    if config[DOMAIN][CONF_DISCOVERY]:
        discovery.load_platform(hass, 'climate', DOMAIN, {}, config)

    return True