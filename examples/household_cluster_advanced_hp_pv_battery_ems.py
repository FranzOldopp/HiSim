"""  Basic household new example. """

# clean

from typing import Optional, Any
import re
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from hisim.simulator import SimulationParameters
from hisim.components import loadprofilegenerator_connector
from hisim.components import weather
from hisim.components import generic_pv_system
from hisim.components import building
from hisim.components import (
    advanced_heat_pump_hplib,
    advanced_battery_bslib,
    controller_l2_energy_management_system,
    simple_hot_water_storage,
    heat_distribution_system,
    generic_heat_pump_modular,
    generic_hot_water_storage_modular,
    controller_l1_heatpump,
    electricity_meter,
)
from hisim.component import ConfigBase
from hisim.result_path_provider import ResultPathProviderSingleton, SortingOptionEnum
from hisim.sim_repository_singleton import SingletonSimRepository, SingletonDictKeyEnum
from hisim.postprocessingoptions import PostProcessingOptions
from hisim import loadtypes as lt
from hisim import log

__authors__ = "Katharina Rieck"
__copyright__ = "Copyright 2022, FZJ-IEK-3"
__credits__ = ["Noah Pflugradt"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Noah Pflugradt"
__status__ = "development"


@dataclass_json
@dataclass
class BuildingPVWeatherConfig(ConfigBase):

    """Configuration for BuildingPv."""

    name: str
    pv_size: float
    pv_azimuth: float
    pv_tilt: float
    pv_power: float
    building_code: str
    total_base_area_in_m2: float
    # location: Any

    @classmethod
    def get_default(cls):
        """Get default BuildingPVConfig."""

        return BuildingPVWeatherConfig(
            name="BuildingPVWeatherConfig",
            pv_size=5,
            pv_azimuth=180,
            pv_tilt=30,
            pv_power=10000,
            building_code="DE.N.SFH.05.Gen.ReEx.001.002",
            total_base_area_in_m2=121.2,
            # location=weather.LocationEnum.Aachen,
        )


def household_cluster_advanced_hp_pv_battery_ems(
    my_sim: Any, my_simulation_parameters: Optional[SimulationParameters] = None
) -> None:  # noqa: too-many-statements
    """Household example.

    This setup function emulates an household including the following components:

    - Simulation Parameters
    - Components
        - Occupancy (Residents' Demands)
        - Weather
        - Photovoltaic System
        - Building
        - Heat Pump
        - Heat Pump Controller
        - Heat Distribution System
        - Heat Distribution Controller
        - Heat Water Storage
        - Battery
        - Energy Management System
        - Domestic water heat pump
        - Electricity Meter
    """

    # =================================================================================================================================
    # Set System Parameters from Config

    # household-pv-config
    config_filename = my_sim.my_module_config_path

    my_config: BuildingPVWeatherConfig
    # if isinstance(config_filename, str) and os.path.exists(config_filename.rstrip("\r")):
    with open(
        config_filename.rstrip("\r"), encoding="unicode_escape"
    ) as system_config_file:
        my_config = BuildingPVWeatherConfig.from_json(system_config_file.read())  # type: ignore

    log.information(f"Read system config from {config_filename}")
    log.information("Config values: " + f"{my_config.to_dict}" + "\n")
    # else:
    #     my_config = BuildingPVWeatherConfig.get_default()
    #     log.information(
    #         "No module config path from the simulator was given. Use default config."
    #     )

    # Set Simulation Parameters
    year = 2021
    seconds_per_timestep = 60

    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters.full_year(
            year=year, seconds_per_timestep=seconds_per_timestep
        )
        my_simulation_parameters.post_processing_options.append(
            PostProcessingOptions.PREPARE_OUTPUTS_FOR_SCENARIO_EVALUATION_WITH_PYAM
        )
        my_simulation_parameters.post_processing_options.append(
            PostProcessingOptions.COMPUTE_OPEX
        )
        my_simulation_parameters.post_processing_options.append(
            PostProcessingOptions.COMPUTE_CAPEX
        )
        my_simulation_parameters.post_processing_options.append(
            PostProcessingOptions.COMPUTE_AND_WRITE_KPIS_TO_REPORT
        )
        my_simulation_parameters.post_processing_options.append(
            PostProcessingOptions.OPEN_DIRECTORY_IN_EXPLORER
        )
    my_sim.set_simulation_parameters(my_simulation_parameters)

    # Set Photovoltaic System
    azimuth = my_config.pv_azimuth
    tilt = my_config.pv_tilt

    # Set Building (scale building according to total base area and not absolute floor area)
    building_code = my_config.building_code
    total_base_area_in_m2 = my_config.total_base_area_in_m2
    absolute_conditioned_floor_area_in_m2 = None

    # # Set Weather
    # location_entry = my_config.location

    # =================================================================================================================================
    # Set Fix System Parameters

    # Set Heat Pump Controller
    hp_controller_mode = (
        2  # mode 1 for on/off and mode 2 for heating/cooling/off (regulated)
    )
    set_heating_threshold_outside_temperature_for_heat_pump_in_celsius = 16.0
    set_cooling_threshold_outside_temperature_for_heat_pump_in_celsius = 22.0
    temperature_offset_for_state_conditions_in_celsius = 5.0

    # Set Heat Pump
    group_id: int = 1  # outdoor/air heat pump (choose 1 for regulated or 4 for on/off)
    heating_reference_temperature_in_celsius: float = (
        -7
    )  # t_in #TODO: get real heating ref temps according to location
    flow_temperature_in_celsius = 21  # t_out_val

    # =================================================================================================================================
    # Build Components

    # Build Heat Distribution Controller
    my_heat_distribution_controller_config = (
        heat_distribution_system.HeatDistributionControllerConfig.get_default_heat_distribution_controller_config()
    )
    my_heat_distribution_controller_config.heating_reference_temperature_in_celsius = (
        heating_reference_temperature_in_celsius
    )
    my_heat_distribution_controller = (
        heat_distribution_system.HeatDistributionController(
            my_simulation_parameters=my_simulation_parameters,
            config=my_heat_distribution_controller_config,
        )
    )
    # Build Building
    my_building_config = building.BuildingConfig.get_default_german_single_family_home()
    my_building_config.heating_reference_temperature_in_celsius = (
        heating_reference_temperature_in_celsius
    )
    my_building_config.building_code = building_code
    my_building_config.total_base_area_in_m2 = total_base_area_in_m2
    my_building_config.absolute_conditioned_floor_area_in_m2 = (
        absolute_conditioned_floor_area_in_m2
    )

    my_building_information = building.BuildingInformation(config=my_building_config)
    my_building = building.Building(
        config=my_building_config, my_simulation_parameters=my_simulation_parameters
    )
    # Build Occupancy
    my_occupancy_config = loadprofilegenerator_connector.OccupancyConfig.get_scaled_CHS01_according_to_number_of_apartments(
        number_of_apartments=my_building_information.number_of_apartments
    )

    my_occupancy = loadprofilegenerator_connector.Occupancy(
        config=my_occupancy_config, my_simulation_parameters=my_simulation_parameters
    )

    # Build Weather
    my_weather_config = weather.WeatherConfig.get_default(
        location_entry=weather.LocationEnum.Aachen
    )

    my_weather = weather.Weather(
        config=my_weather_config, my_simulation_parameters=my_simulation_parameters
    )

    # Build PV
    my_photovoltaic_system_config = (
        generic_pv_system.PVSystemConfig.get_scaled_PV_system(
            rooftop_area_in_m2=my_building_information.scaled_rooftop_area_in_m2
        )
    )
    my_photovoltaic_system_config.azimuth = azimuth
    my_photovoltaic_system_config.tilt = tilt

    my_photovoltaic_system = generic_pv_system.PVSystem(
        config=my_photovoltaic_system_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Pump Controller
    my_heat_pump_controller = advanced_heat_pump_hplib.HeatPumpHplibController(
        config=advanced_heat_pump_hplib.HeatPumpHplibControllerL1Config(
            name="HeatPumpController",
            mode=hp_controller_mode,
            set_heating_threshold_outside_temperature_in_celsius=set_heating_threshold_outside_temperature_for_heat_pump_in_celsius,
            set_cooling_threshold_outside_temperature_in_celsius=set_cooling_threshold_outside_temperature_for_heat_pump_in_celsius,
            temperature_offset_for_state_conditions_in_celsius=temperature_offset_for_state_conditions_in_celsius),
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Pump
    my_heat_pump_config = advanced_heat_pump_hplib.HeatPumpHplibConfig.get_scaled_advanced_hp_lib(
        heating_load_of_building_in_watt=my_building_information.max_thermal_building_demand_in_watt
    )
    my_heat_pump_config.group_id = group_id
    my_heat_pump_config.flow_temperature_in_celsius = flow_temperature_in_celsius
    my_heat_pump_config.heating_reference_temperature_in_celsius = (
        heating_reference_temperature_in_celsius
    )

    my_heat_pump = advanced_heat_pump_hplib.HeatPumpHplib(
        config=my_heat_pump_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Distribution System
    my_heat_distribution_system_config = heat_distribution_system.HeatDistributionConfig.get_default_heatdistributionsystem_config(
        heating_load_of_building_in_watt=my_building_information.max_thermal_building_demand_in_watt
    )
    my_heat_distribution_system = heat_distribution_system.HeatDistribution(
        config=my_heat_distribution_system_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Water Storage
    my_simple_heat_water_storage_config = simple_hot_water_storage.SimpleHotWaterStorageConfig.get_scaled_hot_water_storage(
        heating_load_of_building_in_watt=my_building_information.max_thermal_building_demand_in_watt
    )
    my_simple_hot_water_storage = simple_hot_water_storage.SimpleHotWaterStorage(
        config=my_simple_heat_water_storage_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build EMS
    my_electricity_controller_config = (
        controller_l2_energy_management_system.EMSConfig.get_default_config_ems()
    )
    my_electricity_controller = (
        controller_l2_energy_management_system.L2GenericEnergyManagementSystem(
            my_simulation_parameters=my_simulation_parameters,
            config=my_electricity_controller_config,
        )
    )

    # Build Battery
    my_advanced_battery_config = (
        advanced_battery_bslib.BatteryConfig.get_scaled_battery(
            total_pv_power_in_watt_peak=my_photovoltaic_system_config.power
        )
    )
    my_advanced_battery = advanced_battery_bslib.Battery(
        my_simulation_parameters=my_simulation_parameters,
        config=my_advanced_battery_config,
    )

    # Build DHW (this is taken from household_3_advanced_hp_diesel-car_pv_battery.py)
    my_dhw_heatpump_config = generic_heat_pump_modular.HeatPumpConfig.get_scaled_waterheating_to_number_of_apartments(
        number_of_apartments=my_building_information.number_of_apartments
    )

    my_dhw_heatpump_controller_config = controller_l1_heatpump.L1HeatPumpConfig.get_default_config_heat_source_controller_dhw(
        name="DHWHeatpumpController"
    )

    my_dhw_storage_config = generic_hot_water_storage_modular.StorageConfig.get_scaled_config_for_boiler_to_number_of_apartments(
        number_of_apartments=my_building_information.number_of_apartments
    )
    my_dhw_storage_config.compute_default_cycle(
        temperature_difference_in_kelvin=my_dhw_heatpump_controller_config.t_max_heating_in_celsius
        - my_dhw_heatpump_controller_config.t_min_heating_in_celsius
    )

    my_domnestic_hot_water_storage = generic_hot_water_storage_modular.HotWaterStorage(
        my_simulation_parameters=my_simulation_parameters, config=my_dhw_storage_config
    )

    my_domnestic_hot_water_heatpump_controller = (
        controller_l1_heatpump.L1HeatPumpController(
            my_simulation_parameters=my_simulation_parameters,
            config=my_dhw_heatpump_controller_config,
        )
    )

    my_domnestic_hot_water_heatpump = generic_heat_pump_modular.ModularHeatPump(
        config=my_dhw_heatpump_config, my_simulation_parameters=my_simulation_parameters
    )

    # Build Electricity Meter
    my_electricity_meter = electricity_meter.ElectricityMeter(
        my_simulation_parameters=my_simulation_parameters,
        config=electricity_meter.ElectricityMeterConfig.get_electricity_meter_default_config(),
    )

    # =================================================================================================================================
    # Connect Component Inputs with Outputs

    # Connect PV
    my_photovoltaic_system.connect_only_predefined_connections(my_weather)
    # -----------------------------------------------------------------------------------------------------------------
    # Connect Building
    my_building.connect_only_predefined_connections(my_weather, my_occupancy)
    my_building.connect_input(
        my_building.ThermalPowerDelivered,
        my_heat_distribution_system.component_name,
        my_heat_distribution_system.ThermalPowerDelivered,
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Connect Heat Pump
    my_heat_pump_controller.connect_only_predefined_connections(
        my_weather, my_simple_hot_water_storage, my_heat_distribution_controller
    )

    my_heat_pump.connect_only_predefined_connections(
        my_heat_pump_controller, my_weather, my_simple_hot_water_storage
    )
    # -----------------------------------------------------------------------------------------------------------------
    # Connect Water Storage
    my_simple_hot_water_storage.connect_input(
        my_simple_hot_water_storage.WaterTemperatureFromHeatDistribution,
        my_heat_distribution_system.component_name,
        my_heat_distribution_system.WaterTemperatureOutput,
    )
    my_simple_hot_water_storage.connect_input(
        my_simple_hot_water_storage.WaterTemperatureFromHeatGenerator,
        my_heat_pump.component_name,
        my_heat_pump.TemperatureOutput,
    )
    my_simple_hot_water_storage.connect_input(
        my_simple_hot_water_storage.WaterMassFlowRateFromHeatGenerator,
        my_heat_pump.component_name,
        my_heat_pump.MassFlowOutput,
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Connect Heat Distribution System
    my_heat_distribution_controller.connect_only_predefined_connections(
        my_weather, my_building, my_simple_hot_water_storage
    )
    my_heat_distribution_system.connect_only_predefined_connections(
        my_building, my_heat_distribution_controller, my_simple_hot_water_storage
    )
    # -----------------------------------------------------------------------------------------------------------------
    # Connect DHW
    my_domnestic_hot_water_storage.connect_only_predefined_connections(
        my_occupancy, my_domnestic_hot_water_heatpump
    )

    my_domnestic_hot_water_heatpump_controller.connect_only_predefined_connections(
        my_domnestic_hot_water_storage
    )

    my_domnestic_hot_water_heatpump.connect_only_predefined_connections(
        my_weather, my_domnestic_hot_water_heatpump_controller
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Connect EMS
    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_occupancy,
        source_component_output=my_occupancy.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
        source_weight=999,
    )

    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_domnestic_hot_water_heatpump,
        source_component_output=my_domnestic_hot_water_heatpump.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
        source_weight=999,
    )

    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_heat_pump,
        source_component_output=my_heat_pump.ElectricalInputPower,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.ComponentType.HEAT_PUMP, lt.InandOutputType.ELECTRICITY_REAL],
        source_weight=1,
    )
    my_electricity_controller.add_component_output(
        source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
        source_tags=[
            lt.ComponentType.HEAT_PUMP,
            lt.InandOutputType.ELECTRICITY_TARGET,
        ],
        source_weight=1,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        output_description="Target electricity for Heat Pump. ",
    )
    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_photovoltaic_system,
        source_component_output=my_photovoltaic_system.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_PRODUCTION],
        source_weight=999,
    )

    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_advanced_battery,
        source_component_output=my_advanced_battery.AcBatteryPower,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_REAL],
        source_weight=2,
    )

    electricity_to_or_from_battery_target = (
        my_electricity_controller.add_component_output(
            source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
            source_tags=[
                lt.ComponentType.BATTERY,
                lt.InandOutputType.ELECTRICITY_TARGET,
            ],
            source_weight=2,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            output_description="Target electricity for Battery Control. ",
        )
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Connect Battery
    my_advanced_battery.connect_dynamic_input(
        input_fieldname=advanced_battery_bslib.Battery.LoadingPowerInput,
        src_object=electricity_to_or_from_battery_target,
    )

    # -----------------------------------------------------------------------------------------------------------------
    # Connect Electricity Meter
    my_electricity_meter.add_component_input_and_connect(
        source_component_class=my_electricity_controller,
        source_component_output=my_electricity_controller.ElectricityToOrFromGrid,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_PRODUCTION],
        source_weight=999,
    )

    # =================================================================================================================================
    # Add Components to Simulation Parameters

    my_sim.add_component(my_occupancy)
    my_sim.add_component(my_weather)
    my_sim.add_component(my_photovoltaic_system)
    my_sim.add_component(my_building)
    my_sim.add_component(my_heat_distribution_controller)
    my_sim.add_component(my_heat_distribution_system)
    my_sim.add_component(my_simple_hot_water_storage)
    my_sim.add_component(my_heat_pump_controller)
    my_sim.add_component(my_heat_pump)
    my_sim.add_component(my_domnestic_hot_water_storage)
    my_sim.add_component(my_domnestic_hot_water_heatpump_controller)
    my_sim.add_component(my_domnestic_hot_water_heatpump)
    my_sim.add_component(my_electricity_meter)
    my_sim.add_component(my_advanced_battery)
    my_sim.add_component(my_electricity_controller)

    # Set Results Path
    # if config_filename is given, get hash number and sampling mode for result path
    if config_filename is not None:
        config_filename_splitted = config_filename.split("/")
        hash_number = re.findall(r"\-?\d+", config_filename_splitted[-1])[0]
        sampling_mode = config_filename_splitted[-2]

        sorting_option = SortingOptionEnum.MASS_SIMULATION_WITH_HASH_ENUMERATION

        SingletonSimRepository().set_entry(
            key=SingletonDictKeyEnum.RESULT_SCENARIO_NAME,
            entry=f"{my_simulation_parameters.duration.days}d_{my_simulation_parameters.seconds_per_timestep}s_{hash_number}",
        )
        log.information(
            "Singleton Scenario is set "
            + f"{my_simulation_parameters.duration.days}d_{my_simulation_parameters.seconds_per_timestep}s_{hash_number}"
        )
    # if config_filename is not given, make result path with index enumeration
    else:
        hash_number = None
        sorting_option = SortingOptionEnum.MASS_SIMULATION_WITH_INDEX_ENUMERATION
        sampling_mode = None

    ResultPathProviderSingleton().set_important_result_path_information(
        module_directory=my_sim.module_directory,
        model_name=my_sim.setup_function,
        variant_name=f"{my_simulation_parameters.duration.days}d_{my_simulation_parameters.seconds_per_timestep}s",
        hash_number=hash_number,
        sorting_option=sorting_option,
        sampling_mode=sampling_mode,
    )
