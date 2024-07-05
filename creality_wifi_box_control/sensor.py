from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import datetime, timedelta
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Creality Control sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        CrealitySensor(coordinator, "wanip", "IP Address"),
        CrealitySensor(coordinator, "state", "Current State"),
        CrealitySensor(coordinator, "printProgress", "Job Percentage", unit_of_measurement="%"),
        CrealityTimeSensor(coordinator, "printJobTime", "Time Running"),
        CrealityTimeSensor(coordinator, "printLeftTime", "Time Left"),
        CrealitySensor(coordinator, "completionTime", "Completion Time"),        
        CrealitySensor(coordinator, "print", "Filename"),
        CrealitySensor(coordinator, "nozzleTemp", "Nozzle Temp"),
        CrealitySensor(coordinator, "bedTemp", "Bed Temp"),
        CrealitySensor(coordinator, "err", "Error"),
        CrealitySensor(coordinator, "upgradeStatus", "Upgrade Available"),
        # Add any additional sensors you need here
    ]
    async_add_entities(sensors)

class CrealitySensor(CoordinatorEntity, Entity):
    """Defines a single Creality sensor."""

    def __init__(self, coordinator, data_key, name_suffix, unit_of_measurement=None):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.data_key = data_key
        self._attr_name = f"{self.coordinator.config['model']} {name_suffix}"
        self._attr_unique_id = f"{coordinator.config['host']}_{data_key}"
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return a unique identifier for this sensor."""
        return self._attr_unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        # Special handling for the "Status" sensor to calculate its value
        if self.data_key == "state":
            state = self.coordinator.data.get("state", 0)
            connect = self.coordinator.data.get("connect", 0)        
            if connect == 2:
                return "Offline"
            if state == 1:
                return "Printing"
            if state == 2:
                return "Idle"
            if state == 4:
                return "Error" #Not sure about this one.
            return "Unable to parse status"
        if self.data_key == "err":
            error = self.coordinator.data.get("err", 0)
            if error == 0:
                return "No"
            return "Yes"
        if self.data_key == "upgradeStatus":
            upgradeStatus = self.coordinator.data.get("upgradeStatus", 0)
            if upgradeStatus == 0:
                return "No"
            return "Yes"
        if self.data_key == "completionTime":
            printTimeLeft = self.coordinator.data.get("printLeftTime", 0)
            today = datetime.now()
            completion = today + timedelta(0,printTimeLeft)
            return completion.strftime("%m-%d-%Y %H:%M")
        return self.coordinator.data.get(self.data_key, "Unknown")

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement if defined."""
        return self._unit_of_measurement

    @property
    def device_info(self):
        """Return information about the device this sensor is part of."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.config['host'])},
            "name": "Creality Printer",
            "manufacturer": "Creality",
            "model": {self.coordinator.config['model']}, #Todo set config from the first test connection.
        }

class CrealityTimeSensor(CrealitySensor):
    """Specialized sensor class for handling 'Time' data."""

    @property
    def state(self):
        """Return the state of the sensor, converting time to HH:MM:SS format."""
        time_left = int(self.coordinator.data.get(self.data_key, 0))
        return str(timedelta(seconds=time_left))