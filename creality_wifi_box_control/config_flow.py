import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from aiohttp import ClientSession
import async_timeout
from .const import DOMAIN


class CrealityControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Creality Wifi Box Control."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            valid = await self._test_connection(
                user_input["host"], user_input["port"]
            )
            if valid:
                return self.async_create_entry(title="Creality Wifi Box Control", data=user_input)
            else:
                errors["base"] = "cannot_connect"                
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): cv.string,
                vol.Required("port", default=81): cv.port
            }),
            errors=errors,
        )

    async def _test_connection(self, host, port):
        """Test connection to the Creality printer."""
        uri = f"http://{host}:{port}/protocal.csp?fname=Info&opt=main&function=get"
        try:
            async with ClientSession() as session:
                async with session.get(uri) as resp:                    
                    async with async_timeout.timeout(10):
                        response = await resp.text()
                        if "printProgress" not in response:
                            return False 
                        return True  # Assuming any response with printStatus not TOKEN_ERROR is valid
        except Exception as e:
            return None  # Unable to connect
        return None  # In case the connection could not be established or an unexpected error occurred