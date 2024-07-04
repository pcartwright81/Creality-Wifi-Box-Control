import aiohttp
import async_timeout
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp.ClientSession()
    coordinator = CrealityDataCoordinator(hass, session, entry.data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, 'sensor'))
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, 'button'))
    return True

class CrealityDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, config):
        self.session = session
        self.config = config
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))

    async def _async_update_data(self):
        data = await self.fetch_data()
        if data is None:
            raise UpdateFailed("Failed to fetch data from the Creality Wifi Box.")
        return data

    async def fetch_data(self):
        uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=Info&opt=main&function=get"
        async with self.session.get(uri) as resp:           
            async with async_timeout.timeout(10):
                txt = await resp.text()
                msg = json.loads(txt)
                if msg:
                    return msg
                else:
                    _LOGGER.error("Failed to receive data")
                    return None
   
    async def send_command(self, command):
        """Send a command to the printer."""
        uri = ""
        if command == "PRINT_STOP":
            uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&stop=1"
        if command == "PRINT_PAUSE":
            uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&pause=1"             
        if command == "PRINT_RESUME":
             uri = f"http://{self.config['host']}:{self.config['port']}/protocal.csp?fname=net&opt=iot_conf&function=set&pause=0"
        try:
            async with self.session.get(uri) as resp:           
                async with async_timeout.timeout(10):
                    txt = await resp.text()
                    msg = json.loads(txt)              
                    if msg.get("error") == "0":
                        _LOGGER.info(f"Command {command} executed successfully.")
                    else:
                        _LOGGER.error(f"Command {command} failed.")                    
        except Exception as e:
            _LOGGER.error(f"Failed to send command {command}: {e}")