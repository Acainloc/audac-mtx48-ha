from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_ZONES

# Schéma de configuration initiale (ajout de l'intégration)
DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Optional("port", default=DEFAULT_PORT): int,
    vol.Optional("zones", default=DEFAULT_ZONES): vol.In([4, 8]),
    vol.Optional("device_id", default="M001"): str,
    vol.Optional("source_id", default="F001"): str,
})

class AudacConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flow de configuration pour l'intégration AUDAC MTX."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Création de l'entrée de configuration
            return self.async_create_entry(
                title=f"AUDAC MTX ({user_input['host']})",
                data=user_input,
            )
        # Affiche le formulaire initial
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Retourne le flow d'options (appelé par Home Assistant côté classe)."""
        return AudacOptionsFlow(config_entry)

class AudacOptionsFlow(config_entries.OptionsFlow):
    """Flow pour la configuration des options de l'intégration (après installation)."""

    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        # Enregistre les options si l'utilisateur a soumis le formulaire
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Valeurs par défaut si absentes
        current_poll = self.entry.options.get("poll_interval", 5)

        # Formulaire d'options
        schema = vol.Schema({
            vol.Optional("poll_interval", default=current_poll): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
