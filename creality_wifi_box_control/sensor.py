from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Creality Control sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        CrealitySensor(coordinator, "model", "Model"),
        CrealitySensor(coordinator, "wanip", "IP Address"),
        CrealitySensor(coordinator, "state", "Current State"),
        CrealitySensor(coordinator, "printProgress", "Job Percentage", unit_of_measurement="%"),
        CrealityTimeLeftSensor(coordinator, "printLeftTime", "Time Left"),
        # CrealitySensor(coordinator, "print", "Filename"),
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
        self._attr_name = f"Creality {name_suffix}"
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
            if state == 1:
                return "Printing"
            if state == 2:
                return "Idle"
            if state == 4:
                return "Offline"
            return "Unable to parse status"
        if self.data_key == "err":
            error = self.coordinator.data.get("err", 0)
            if error == 0:
                return "No"
            if error > 0:
                return "Yes"
        if self.data_key == "upgradeStatus":
            error = self.coordinator.data.get("upgradeStatus", 0)
            if error == 0:
                return "No"
            if error == 1:
                return "Yes"
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
            "model": "Creality Printer",  # Update with your model, have not found a way to get this information
        }

class CrealityTimeLeftSensor(CrealitySensor):
    """Specialized sensor class for handling 'Time Left' data."""

    @property
    def state(self):
        """Return the state of the sensor, converting time to HH:MM:SS format."""
        time_left = int(self.coordinator.data.get(self.data_key, 0))
        return str(timedelta(seconds=time_left))