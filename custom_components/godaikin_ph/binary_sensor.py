"""Binary sensor platform for GO DAIKIN integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GodaikinDataUpdateCoordinator
from .types import Aircond, UniqueID


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GO DAIKIN binary sensor entities from a config entry."""
    coordinator: GodaikinDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        GodaikinCompressorRunningSensor(coordinator, unique_id)
        for unique_id in coordinator.data.keys()
    )


class GodaikinCompressorRunningSensor(
    CoordinatorEntity[GodaikinDataUpdateCoordinator], BinarySensorEntity
):
    """Compressor running indicator for GO DAIKIN air conditioner."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the compressor running sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._attr_unique_id = f"{unique_id}_compressor_running"
        self._attr_name = f"{coordinator.data[unique_id].ACName} Compressor Running"

    @property
    def aircond(self) -> Aircond:
        """Return the air conditioner data."""
        return self.coordinator.data[self._unique_id]

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.aircond.is_connected

    @property
    def is_on(self) -> bool:
        """Return true if the compressor is running."""
        return bool(self.aircond.shadowState.Sta_CpOnOff)
