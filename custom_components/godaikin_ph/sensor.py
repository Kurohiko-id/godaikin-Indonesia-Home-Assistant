"""Sensor platform for GO DAIKIN integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GodaikinDataUpdateCoordinator
from .types import Aircond, UniqueID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GO DAIKIN sensor entities from a config entry."""
    coordinator: GodaikinDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for unique_id in coordinator.data.keys():
        entities.extend(
            [
                GodaikinPowerSensor(coordinator, unique_id),
                GodaikinIndoorTempSensor(coordinator, unique_id),
                GodaikinOutdoorTempSensor(coordinator, unique_id),
                GodaikinEnergySensor(coordinator, unique_id),
                GodaikinMoldProofRemainingSensor(coordinator, unique_id),
                GodaikinTimerStateSensor(coordinator, unique_id),
                GodaikinErrorCodeSensor(coordinator, unique_id),
                GodaikinCompressorFrequencySensor(coordinator, unique_id),
                GodaikinCurrentSensor(coordinator, unique_id),
                GodaikinIndoorCoilTempSensor(coordinator, unique_id),
                GodaikinOutdoorCoilTempSensor(coordinator, unique_id),
                GodaikinDischargeTempSensor(coordinator, unique_id),
                GodaikinIndoorFanRpmSensor(coordinator, unique_id),
                GodaikinOutdoorFanRpmSensor(coordinator, unique_id),
            ]
        )
        # Units without a humidity sensor report Sta_IDRh as 0 when off and
        # 255 (invalid sentinel, not a real relative-humidity reading) when
        # on. Only create the entity for units that reported a plausible
        # in-range value at least once.
        if 0 < coordinator.data[unique_id].shadowState.Sta_IDRh <= 100:
            entities.append(GodaikinHumiditySensor(coordinator, unique_id))

    async_add_entities(entities)


class GodaikinSensorBase(
    CoordinatorEntity[GodaikinDataUpdateCoordinator], SensorEntity
):
    """Base class for GO DAIKIN sensors."""

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{unique_id}_{sensor_type}"

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


class GodaikinPowerSensor(GodaikinSensorBase):
    """Power consumption sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator, unique_id, "power")
        self._attr_name = f"{self.aircond.ACName} Power"

    @property
    def native_value(self) -> float | None:
        """Return the power consumption."""
        return self.aircond.shadowState.Sta_ODPwrCon


class GodaikinIndoorTempSensor(GodaikinSensorBase):
    """Indoor temperature sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the indoor temperature sensor."""
        super().__init__(coordinator, unique_id, "indoor_temperature")
        self._attr_name = f"{self.aircond.ACName} Indoor Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the indoor temperature."""
        return self.aircond.shadowState.Sta_IDRoomTemp


class GodaikinOutdoorTempSensor(GodaikinSensorBase):
    """Outdoor temperature sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the outdoor temperature sensor."""
        super().__init__(coordinator, unique_id, "outdoor_temperature")
        self._attr_name = f"{self.aircond.ACName} Outdoor Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the outdoor temperature."""
        return self.aircond.shadowState.Sta_ODAirTemp


class GodaikinHumiditySensor(GodaikinSensorBase):
    """Indoor humidity sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, unique_id, "indoor_humidity")
        self._attr_name = f"{self.aircond.ACName} Indoor Humidity"

    @property
    def native_value(self) -> float | None:
        """Return the indoor relative humidity."""
        humidity = self.aircond.shadowState.Sta_IDRh
        return humidity if 0 < humidity <= 100 else None


class GodaikinEnergySensor(GodaikinSensorBase):
    """Energy consumption sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, unique_id, "energy")
        self._attr_name = f"{self.aircond.ACName} Energy"

    @property
    def native_value(self) -> float | None:
        """Return the energy consumption."""
        return round(self.coordinator.get_energy_usage(self._unique_id), 2)


class GodaikinMoldProofRemainingSensor(GodaikinSensorBase):
    """Mold-proof remaining time sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the mold-proof remaining sensor."""
        super().__init__(coordinator, unique_id, "mold_proof_remaining")
        self._attr_name = f"{self.aircond.ACName} Mold-proof remaining"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success or not self.aircond.is_connected:
            return False
        if not self.coordinator.mold_proof:
            return False
        return self.coordinator.mold_proof.is_active(self._unique_id)

    @property
    def native_value(self) -> float | None:
        """Return the remaining mold-proof time in minutes."""
        if not self.coordinator.mold_proof:
            return None
        if not self.coordinator.mold_proof.is_active(self._unique_id):
            return None
        remaining_seconds = self.coordinator.mold_proof.get_remaining_time(
            self._unique_id
        )
        return round(remaining_seconds / 60, 1)


class GodaikinTimerStateSensor(GodaikinSensorBase):
    """Diagnostic sensor exposing the raw timer/schedule fields.

    GO DAIKIN units expose timer and schedule state, but the exact encoding
    of these fields is not yet decoded. This sensor surfaces the raw values so
    that an armed timer/schedule can be observed and reverse-engineered. Its
    state is ``timerState``; ``Bar_Timer`` and ``sch`` are extra attributes.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the timer-state diagnostic sensor."""
        super().__init__(coordinator, unique_id, "timer_state")
        self._attr_name = f"{self.aircond.ACName} Timer state"

    @property
    def native_value(self) -> int | None:
        """Return the raw timer state value."""
        return self.aircond.shadowState.timerState

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the related raw timer/schedule flags."""
        shadow = self.aircond.shadowState
        return {
            "bar_timer": shadow.Bar_Timer,
            "sch": shadow.sch,
        }


class GodaikinErrorCodeSensor(GodaikinSensorBase):
    """Diagnostic sensor exposing the raw error code."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the error code sensor."""
        super().__init__(coordinator, unique_id, "error_code")
        self._attr_name = f"{self.aircond.ACName} Error Code"

    @property
    def native_value(self) -> int | None:
        """Return the raw error code (0 = normal)."""
        return self.aircond.shadowState.Sta_ErrCode


class GodaikinCompressorFrequencySensor(GodaikinSensorBase):
    """Compressor frequency sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the compressor frequency sensor."""
        super().__init__(coordinator, unique_id, "compressor_frequency")
        self._attr_name = f"{self.aircond.ACName} Compressor Frequency"

    @property
    def native_value(self) -> float | None:
        """Return the outdoor compressor frequency."""
        return self.aircond.shadowState.Sta_ODCpFreq


class GodaikinCurrentSensor(GodaikinSensorBase):
    """Outdoor unit current sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the current sensor."""
        super().__init__(coordinator, unique_id, "current")
        self._attr_name = f"{self.aircond.ACName} Current"

    @property
    def native_value(self) -> float | None:
        """Return the outdoor unit current draw."""
        return self.aircond.shadowState.Sta_ODCurrConsp


class GodaikinIndoorCoilTempSensor(GodaikinSensorBase):
    """Indoor coil temperature sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the indoor coil temperature sensor."""
        super().__init__(coordinator, unique_id, "indoor_coil_temperature")
        self._attr_name = f"{self.aircond.ACName} Indoor Coil Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the indoor coil temperature."""
        return self.aircond.shadowState.Sta_IDCoilTemp


class GodaikinOutdoorCoilTempSensor(GodaikinSensorBase):
    """Outdoor coil temperature sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the outdoor coil temperature sensor."""
        super().__init__(coordinator, unique_id, "outdoor_coil_temperature")
        self._attr_name = f"{self.aircond.ACName} Outdoor Coil Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the outdoor coil temperature."""
        return self.aircond.shadowState.Sta_ODCoilTemp


class GodaikinDischargeTempSensor(GodaikinSensorBase):
    """Compressor discharge temperature sensor for GO DAIKIN air conditioner."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the discharge temperature sensor."""
        super().__init__(coordinator, unique_id, "discharge_temperature")
        self._attr_name = f"{self.aircond.ACName} Discharge Temperature"

    @property
    def native_value(self) -> float | None:
        """Return the outdoor compressor discharge temperature."""
        return self.aircond.shadowState.Sta_ODDiscTemp


class GodaikinIndoorFanRpmSensor(GodaikinSensorBase):
    """Indoor fan RPM sensor for GO DAIKIN air conditioner."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "rpm"

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the indoor fan RPM sensor."""
        super().__init__(coordinator, unique_id, "indoor_fan_rpm")
        self._attr_name = f"{self.aircond.ACName} Indoor Fan RPM"

    @property
    def native_value(self) -> int | None:
        """Return the indoor fan speed."""
        return self.aircond.shadowState.Sta_IDRPM


class GodaikinOutdoorFanRpmSensor(GodaikinSensorBase):
    """Outdoor fan RPM sensor for GO DAIKIN air conditioner."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "rpm"

    def __init__(
        self,
        coordinator: GodaikinDataUpdateCoordinator,
        unique_id: UniqueID,
    ) -> None:
        """Initialize the outdoor fan RPM sensor."""
        super().__init__(coordinator, unique_id, "outdoor_fan_rpm")
        self._attr_name = f"{self.aircond.ACName} Outdoor Fan RPM"

    @property
    def native_value(self) -> int | None:
        """Return the outdoor fan speed."""
        return self.aircond.shadowState.Sta_ODRPM
