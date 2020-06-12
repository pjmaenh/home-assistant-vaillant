""" Support for Vaillant vSmart and Bulex Migo Thermostats."""
from datetime import timedelta
import logging
from typing import Optional, List
import time

#import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_OFF,
    PRESET_AWAY,
    CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF,
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE,
    DEFAULT_MIN_TEMP
)
from homeassistant.const import (
    TEMP_CELSIUS, ATTR_TEMPERATURE, PRECISION_HALVES, STATE_OFF,
    ATTR_BATTERY_LEVEL
)
from homeassistant.util import Throttle

from .const import DATA_VAILLANT_AUTH

_LOGGER = logging.getLogger(__name__)

PRESET_HWB = 'Hot Water Boost'
#PRESET_FROSTGUARD = 'Frostguard'
PRESET_SUMMER = 'Summer'
PRESET_WINTER = 'Winter'

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE)
SUPPORT_HVAC = [HVAC_MODE_HEAT, HVAC_MODE_AUTO, HVAC_MODE_OFF]
SUPPORT_PRESET = [PRESET_AWAY, PRESET_HWB, PRESET_SUMMER, PRESET_WINTER]

#CONF_THERMOSTAT = 'thermostat'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Vaillant Thermostat."""
    import pyvaillant
    auth = hass.data[DATA_VAILLANT_AUTH]

    try:
        data = ThermostatData(auth)
    except pyvaillant.NoDevice:
        return

    data.update()
    devices = []
    devices.append(VaillantThermostat(data))
    add_entities(devices, True)
    

class VaillantThermostat(ClimateEntity):
    """Representation a Vaillant thermostat."""

    def __init__(self, data):
        """Initialize the sensor."""
        self._data = data
        self._previous_system_mode = None
        #self._state = None
        self._name = None
        self._current_temperature = None
        self._target_temperature = None
        self.update_without_throttle = False

        # todo
        #self._operation_list.append(HVAC_MODE_OFF)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._data.thermostatdata.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._data.thermostatdata.temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._data.thermostatdata.setpoint_temp


    @property
    def hvac_mode(self):
        """
        Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self._data.thermostatdata.system_mode == "frostguard":
            return HVAC_MODE_OFF
        elif 'manual' in self._data.thermostatdata.setpoint_modes:
            return HVAC_MODE_HEAT
        elif 'hwb' in self._data.thermostatdata.setpoint_modes:
            return HVAC_MODE_HEAT
        return HVAC_MODE_AUTO
        

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return SUPPORT_HVAC

    @property
    def hvac_action(self) -> Optional[str]:
        """
        Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        if self._data.thermostatdata.system_mode == "frostguard":
            return CURRENT_HVAC_OFF

        if self.current_temperature < self.target_temperature:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        #ToDo !
        if hvac_mode == HVAC_MODE_OFF:
            prev = self._data.thermostatdata.system_mode
            if (prev != "frostguard"):
                self._previous_system_mode = prev
            self._data.thermostatdata.setSystemMode("frostguard")
        elif hvac_mode == HVAC_MODE_HEAT:
            self._data.thermostatdata.activate("hwb", None, 3600)
        elif hvac_mode == HVAC_MODE_AUTO:
            if self._previous_system_mode:
                self._data.thermostatdata.setSystemMode(self._previous_system_mode)
            self._data.thermostatdata.reset()

        self.update_without_throttle = True
        self.schedule_update_ha_state(True)

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        #ToDo !
        if preset_mode == PRESET_AWAY:
            self._data.thermostatdata.activate("away", None)

        elif preset_mode == PRESET_HWB:
            self._data.thermostatdata.activate("hwb", None, 3600)

        elif preset_mode == PRESET_SUMMER:
            if(self._data.thermostatdata.system_mode != "summer"):
                self._data.thermostatdata.setSystemMode("summer")
            self._data.thermostatdata.reset()

        elif preset_mode == PRESET_WINTER:
            if(self._data.thermostatdata.system_mode != "winter"):
                self._data.thermostatdata.setSystemMode("winter")
            self._data.thermostatdata.reset()
        else:
            _LOGGER.error("Preset mode '%s' not available", preset_mode)

        self.update_without_throttle = True
        self.schedule_update_ha_state(True)

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode, e.g., home, away, temp."""
        if 'away' in self._data.thermostatdata.setpoint_modes:
            return PRESET_AWAY
        elif 'hwb' in self._data.thermostatdata.setpoint_modes:
            return PRESET_HWB
        elif 'manual' in self._data.thermostatdata.setpoint_modes:
            return 'Manual'
        elif self._data.thermostatdata.system_mode == "summer":
            return PRESET_SUMMER
        elif self._data.thermostatdata.system_mode == "winter":
            return PRESET_WINTER

    @property
    def preset_modes(self) -> Optional[List[str]]:
        """Return a list of available preset modes."""
        return SUPPORT_PRESET

    def set_temperature(self, **kwargs):
        """Set new target temperature for 2 hours."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        self._data.thermostatdata.activate("manual", temperature)
        
    def update(self):
        """Get the latest data from Vaillant API and updates the states."""

        if self.update_without_throttle:
            self._data.update(no_throttle=True)
            self.update_without_throttle = False
        else:
            self._data.update()


class ThermostatData:
    """Get the latest data from Vaillant."""

    def __init__(self, auth):
        """Initialize the data object."""
        self.auth = auth
        self.thermostatdata = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Call the Vaillant API to update the data."""
        import pyvaillant
        self.thermostatdata = pyvaillant.VaillantThermostatData(self.auth)

