"""  Household example with advanced heat pump, electric car, PV and battery. """

# clean

from typing import List, Optional, Any
from os import listdir
from pathlib import Path
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from utspclient.helpers.lpgdata import (
    ChargingStationSets,
    Households,
    TransportationDeviceSets,
    TravelRouteSets,
)

from hisim.simulator import SimulationParameters
from hisim.components import loadprofilegenerator_utsp_connector
from hisim.components import weather
from hisim.components import advanced_heat_pump_hplib
from hisim.components import heat_distribution_system
from hisim.components import building
from hisim.components import simple_hot_water_storage
from hisim.components import generic_car
from hisim.components import generic_heat_pump_modular
from hisim.components import controller_l1_heatpump
from hisim.components import generic_hot_water_storage_modular
from hisim.components import electricity_meter
from hisim.components import generic_pv_system
from hisim.components import advanced_battery_bslib
from hisim.components import advanced_ev_battery_bslib
from hisim.components import controller_l1_generic_ev_charge
from hisim.components import controller_l2_energy_management_system
from hisim.components.configuration import HouseholdWarmWaterDemandConfig
from hisim import utils
from hisim import loadtypes as lt
from hisim import log
from examples.modular_example import cleanup_old_lpg_requests

__authors__ = "Markus Blasberg"
__copyright__ = "Copyright 2023, FZJ-IEK-3"
__credits__ = ["Noah Pflugradt"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Markus Blasberg"
__status__ = "development"


@dataclass_json
@dataclass
class HouseholdAdvancedHpEvPvBatteryConfig:

    """Configuration for with advanced heat pump, electric car, PV and battery."""

    building_type: str
    number_of_apartments: int
    # dhw_controlable: bool  # if dhw is controlled by EMS
    # heatpump_controlable: bool  # if heatpump is controlled by EMS
    surplus_control: bool  # decision on the consideration of smart control for heat pump and dhw, increase storage temperatures
    surplus_control_building_temperature_modifier: bool  # increase set_room_temperature in case of surplus electricity
    surplus_control_car: bool  # decision on the consideration of smart control for EV charging
    # simulation_parameters: SimulationParameters
    # total_base_area_in_m2: float
    occupancy_config: loadprofilegenerator_utsp_connector.UtspLpgConnectorConfig
    pv_config: generic_pv_system.PVSystemConfig
    building_config: building.BuildingConfig
    hds_controller_config: heat_distribution_system.HeatDistributionControllerConfig
    hds_config: heat_distribution_system.HeatDistributionConfig
    hp_controller_config: advanced_heat_pump_hplib.HeatPumpHplibControllerL1Config
    hp_config: advanced_heat_pump_hplib.HeatPumpHplibConfig
    simple_hot_water_storage_config: simple_hot_water_storage.SimpleHotWaterStorageConfig
    dhw_heatpump_config: generic_heat_pump_modular.HeatPumpConfig
    dhw_heatpump_controller_config: controller_l1_heatpump.L1HeatPumpConfig
    dhw_storage_config: generic_hot_water_storage_modular.StorageConfig
    car_config: generic_car.CarConfig
    car_battery_config: advanced_ev_battery_bslib.CarBatteryConfig
    car_battery_controller_config: controller_l1_generic_ev_charge.ChargingStationConfig
    electricity_meter_config: electricity_meter.ElectricityMeterConfig
    advanced_battery_config: advanced_battery_bslib.BatteryConfig
    electricity_controller_config: controller_l2_energy_management_system.EMSConfig

    @classmethod
    def get_default(cls):
        """Get default HouseholdAdvancedHpEvPvBatteryConfig."""

        # set number of apartments (mandatory for dhw storage config)
        number_of_apartments = 1

        charging_station_set = ChargingStationSets.Charging_At_Home_with_11_kW
        charging_power = float(
            (charging_station_set.Name or "").split("with ")[1].split(" kW")[0]
        )
        heating_reference_temperature_in_celsius: float = -7
        set_heating_threshold_outside_temperature_in_celsius: float = 16.0

        building_config = (
            building.BuildingConfig.get_default_german_single_family_home()
        )
        my_building_information = building.BuildingInformation(config=building_config)

        household_config = HouseholdAdvancedHpEvPvBatteryConfig(
            building_type="blub",
            number_of_apartments=number_of_apartments,
            # dhw_controlable=False,
            # heatpump_controlable=False,
            surplus_control=False,
            surplus_control_building_temperature_modifier=False,
            surplus_control_car=False,
            # simulation_parameters=SimulationParameters.one_day_only(2022),
            # total_base_area_in_m2=121.2,
            occupancy_config=loadprofilegenerator_utsp_connector.UtspLpgConnectorConfig(
                url="http://134.94.131.167:443/api/v1/profilerequest",
                api_key="OrjpZY93BcNWw8lKaMp0BEchbCc",
                household=Households.CHR01_Couple_both_at_Work,
                result_path=utils.HISIMPATH["results"],
                travel_route_set=TravelRouteSets.Travel_Route_Set_for_10km_Commuting_Distance,
                transportation_device_set=TransportationDeviceSets.Bus_and_one_30_km_h_Car,
                charging_station_set=charging_station_set,
                name="UTSPConnector",
                consumption=0.0,
                profile_with_washing_machine_and_dishwasher=True,
            ),
            pv_config=generic_pv_system.PVSystemConfig.get_default_PV_system(),
            building_config=building_config,
            hds_controller_config=(
                heat_distribution_system.HeatDistributionControllerConfig.get_default_heat_distribution_controller_config()
            ),
            hds_config=(
                heat_distribution_system.HeatDistributionConfig.get_default_heatdistributionsystem_config(
                    heating_load_of_building_in_watt=my_building_information.max_thermal_building_demand_in_watt
                )
            ),
            hp_controller_config=advanced_heat_pump_hplib.HeatPumpHplibControllerL1Config.get_default_generic_heat_pump_controller_config(),
            hp_config=advanced_heat_pump_hplib.HeatPumpHplibConfig.get_default_generic_advanced_hp_lib(),
            simple_hot_water_storage_config=(
                simple_hot_water_storage.SimpleHotWaterStorageConfig.get_default_simplehotwaterstorage_config()
            ),
            dhw_heatpump_config=(
                generic_heat_pump_modular.HeatPumpConfig.get_default_config_waterheating()
            ),
            dhw_heatpump_controller_config=controller_l1_heatpump.L1HeatPumpConfig.get_default_config_heat_source_controller_dhw(
                name="DHWHeatpumpController"
            ),
            dhw_storage_config=(
                generic_hot_water_storage_modular.StorageConfig.get_default_config_for_boiler()
            ),
            car_config=generic_car.CarConfig.get_default_ev_config(),
            car_battery_config=advanced_ev_battery_bslib.CarBatteryConfig.get_default_config(),
            car_battery_controller_config=(
                controller_l1_generic_ev_charge.ChargingStationConfig.get_default_config(
                    charging_station_set=charging_station_set
                )
            ),
            electricity_meter_config=electricity_meter.ElectricityMeterConfig.get_electricity_meter_default_config(),
            advanced_battery_config=advanced_battery_bslib.BatteryConfig.get_default_config(),
            electricity_controller_config=(
                controller_l2_energy_management_system.EMSConfig.get_default_config_ems()
            ),
        )
        # adjust HeatPump
        household_config.hp_config.group_id = 1  # use modulating heatpump as default
        household_config.hp_controller_config.mode = (
            2  # use heating and cooling as default
        )
        household_config.hp_config.set_thermal_output_power_in_watt = (
            6000  # default value leads to switching on-off very often
        )
        household_config.hp_config.minimum_idle_time_in_seconds = (
            900  # default value leads to switching on-off very often
        )
        household_config.hp_config.minimum_running_time_in_seconds = (
            900  # default value leads to switching on-off very often
        )

        # set same heating threshold
        household_config.hds_controller_config.set_heating_threshold_outside_temperature_in_celsius = (
            set_heating_threshold_outside_temperature_in_celsius
        )
        household_config.hp_controller_config.set_heating_threshold_outside_temperature_in_celsius = (
            set_heating_threshold_outside_temperature_in_celsius
        )

        # set same heating reference temperature
        household_config.hds_controller_config.heating_reference_temperature_in_celsius = (
            heating_reference_temperature_in_celsius
        )
        household_config.hp_config.heating_reference_temperature_in_celsius = (
            heating_reference_temperature_in_celsius
        )
        household_config.building_config.heating_reference_temperature_in_celsius = (
            heating_reference_temperature_in_celsius
        )

        household_config.hp_config.flow_temperature_in_celsius = 21  # Todo: check value

        # set dhw storage volume, because default(volume = 230) leads to an error
        household_config.dhw_storage_config.volume = 250

        # set charging power from battery and controller to same value, to reduce error in simulation of battery
        household_config.car_battery_config.p_inv_custom = charging_power * 1e3

        return household_config


def household_5_advanced_hp_ev_pv_battery(
    my_sim: Any, my_simulation_parameters: Optional[SimulationParameters] = None
) -> None:  # noqa: too-many-statements
    """Example with advanced hp and EV and PV and battery.

    This setup function emulates a household with some basic components. Here the residents have their
    electricity and heating needs covered by a the advanced heat pump.

    - Simulation Parameters
    - Components
        - Occupancy (Residents' Demands)
        - Weather
        - Building
        - PV
        - Electricity Meter
        - Advanced Heat Pump HPlib
        - Advanced Heat Pump HPlib Controller
        - Heat Distribution System
        - Heat Distribution System Controller
        - Simple Hot Water Storage

        - DHW (Heatpump, Heatpumpcontroller, Storage; copied from modular_example)
        - Car (Electric Vehicle, Electric Vehicle Battery, Electric Vehicle Battery Controller)
        - Battery
        - EMS (necessary for Battery and Electric Vehicle)
    """

    # cleanup old lpg requests, mandatory to change number of cars
    # Todo: change cleanup-function if result_path from occupancy is not utils.HISIMPATH["results"]
    if Path(utils.HISIMPATH["utsp_results"]).exists():
        cleanup_old_lpg_requests()

    config_filename = "household_5_advanced_hp_ev_pv_battery_config.json"

    my_config: HouseholdAdvancedHpEvPvBatteryConfig
    if Path(config_filename).is_file():
        with open(config_filename, encoding="utf8") as system_config_file:
            my_config = HouseholdAdvancedHpEvPvBatteryConfig.from_json(system_config_file.read())  # type: ignore
        log.information(f"Read system config from {config_filename}")
    else:
        my_config = HouseholdAdvancedHpEvPvBatteryConfig.get_default()

        # Todo: save file leads to use of file in next run. File was just produced to check how it looks like
        # my_config_json = my_config.to_json()
        # with open(config_filename, "w", encoding="utf8") as system_config_file:
        #     system_config_file.write(my_config_json)

    # =================================================================================================================================
    # Set System Parameters

    # Set Simulation Parameters
    year = 2021
    seconds_per_timestep = 60

    # =================================================================================================================================
    # Build Components

    # Build Simulation Parameters
    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters.full_year_all_options(
            year=year, seconds_per_timestep=seconds_per_timestep
        )
    my_simulation_parameters.surplus_control = (
        my_config.surplus_control_car
    )  # EV charger is controlled by simulation_parameters
    clever = my_config.surplus_control
    my_sim.set_simulation_parameters(my_simulation_parameters)

    # Build heat Distribution System Controller
    my_heat_distribution_controller = (
        heat_distribution_system.HeatDistributionController(
            config=my_config.hds_controller_config,
            my_simulation_parameters=my_simulation_parameters,
        )
    )

    # Build Occupancy
    my_occupancy_config = my_config.occupancy_config
    my_occupancy = loadprofilegenerator_utsp_connector.UtspLpgConnector(
        config=my_occupancy_config, my_simulation_parameters=my_simulation_parameters
    )

    # Build Weather
    my_weather = weather.Weather(
        config=weather.WeatherConfig.get_default(weather.LocationEnum.Aachen),
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build PV
    my_photovoltaic_system = generic_pv_system.PVSystem(
        config=my_config.pv_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Building
    my_building = building.Building(
        config=my_config.building_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Distribution System
    my_heat_distribution = heat_distribution_system.HeatDistribution(
        my_simulation_parameters=my_simulation_parameters, config=my_config.hds_config
    )

    # Build Heat Pump Controller
    my_heat_pump_controller_config = my_config.hp_controller_config
    my_heat_pump_controller_config.name = "HeatPumpHplibController"

    my_heat_pump_controller = advanced_heat_pump_hplib.HeatPumpHplibController(
        config=my_heat_pump_controller_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Pump
    my_heat_pump_config = my_config.hp_config
    my_heat_pump_config.name = "HeatPumpHPLib"

    my_heat_pump = advanced_heat_pump_hplib.HeatPumpHplib(
        config=my_heat_pump_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build Heat Water Storage
    my_simple_hot_water_storage = simple_hot_water_storage.SimpleHotWaterStorage(
        config=my_config.simple_hot_water_storage_config,
        my_simulation_parameters=my_simulation_parameters,
    )

    # Build DHW
    my_dhw_heatpump_config = my_config.dhw_heatpump_config
    my_dhw_heatpump_config.power_th = (
        my_occupancy.max_hot_water_demand
        * (4180 / 3600)
        * 0.5
        * (3600 / my_simulation_parameters.seconds_per_timestep)
        * (
            HouseholdWarmWaterDemandConfig.ww_temperature_demand
            - HouseholdWarmWaterDemandConfig.freshwater_temperature
        )
    )

    my_dhw_heatpump_controller_config = my_config.dhw_heatpump_controller_config

    my_dhw_storage_config = my_config.dhw_storage_config
    my_dhw_storage_config.name = "DHWStorage"
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

    # Build Electric Vehicle(s)
    # get names of all available cars
    filepaths = listdir(utils.HISIMPATH["utsp_results"])
    filepaths_location = [elem for elem in filepaths if "CarLocation." in elem]
    names = [elem.partition(",")[0].partition(".")[2] for elem in filepaths_location]

    my_car_config = (
        my_config.car_config
    )  # Todo: check source weight in case of 2 vehicles
    my_car_config.name = "ElectricCar"

    # create all cars
    my_cars: List[generic_car.Car] = []
    for car in names:
        # Todo: check car name in case of 1 vehicle
        my_car_config.name = car
        my_cars.append(
            generic_car.Car(
                my_simulation_parameters=my_simulation_parameters,
                config=my_car_config,
                occupancy_config=my_occupancy_config,
            )
        )

    # Build Electric Vehicle Battery
    my_car_batteries: List[advanced_ev_battery_bslib.CarBattery] = []
    my_car_battery_controllers: List[controller_l1_generic_ev_charge.L1Controller] = []
    car_number = 1
    for car in my_cars:
        my_car_battery_config = my_config.car_battery_config
        my_car_battery_config.source_weight = car.config.source_weight
        my_car_battery_config.name = f"CarBattery_{car_number}"
        my_car_battery = advanced_ev_battery_bslib.CarBattery(
            my_simulation_parameters=my_simulation_parameters,
            config=my_car_battery_config,
        )
        my_car_batteries.append(my_car_battery)

        my_car_battery_controller_config = my_config.car_battery_controller_config
        my_car_battery_controller_config.source_weight = car.config.source_weight
        my_car_battery_controller_config.name = f"L1EVChargeControl_{car_number}"
        my_car_battery_controller_config.battery_set = (
            0.4  # lower threshold for soc of car battery in clever case
        )

        my_car_battery_controller = controller_l1_generic_ev_charge.L1Controller(
            my_simulation_parameters=my_simulation_parameters,
            config=my_car_battery_controller_config,
        )
        my_car_battery_controllers.append(my_car_battery_controller)

        car_number += 1

    # Build Electricity Meter
    my_electricity_meter = electricity_meter.ElectricityMeter(
        my_simulation_parameters=my_simulation_parameters,
        config=my_config.electricity_meter_config,
    )

    # Build EMS
    my_electricity_controller = (
        controller_l2_energy_management_system.L2GenericEnergyManagementSystem(
            my_simulation_parameters=my_simulation_parameters,
            config=my_config.electricity_controller_config,
        )
    )

    # Build Battery
    my_advanced_battery = advanced_battery_bslib.Battery(
        my_simulation_parameters=my_simulation_parameters,
        config=my_config.advanced_battery_config,
    )

    # =================================================================================================================================
    # Connect Component Inputs with Outputs

    my_photovoltaic_system.connect_only_predefined_connections(my_weather)

    my_building.connect_only_predefined_connections(my_weather, my_occupancy)
    my_building.connect_input(
        my_building.ThermalPowerDelivered,
        my_heat_distribution.component_name,
        my_heat_distribution.ThermalPowerDelivered,
    )

    my_heat_pump_controller.connect_only_predefined_connections(
        my_weather, my_simple_hot_water_storage, my_heat_distribution_controller
    )

    my_heat_pump.connect_only_predefined_connections(
        my_heat_pump_controller, my_weather, my_simple_hot_water_storage
    )

    my_heat_distribution_controller.connect_only_predefined_connections(
        my_weather, my_building, my_simple_hot_water_storage
    )

    my_heat_distribution.connect_only_predefined_connections(
        my_heat_distribution_controller, my_building, my_simple_hot_water_storage
    )

    my_simple_hot_water_storage.connect_input(
        my_simple_hot_water_storage.WaterTemperatureFromHeatDistribution,
        my_heat_distribution.component_name,
        my_heat_distribution.WaterTemperatureOutput,
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

    # connect DHW
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
    # connect Electric Vehicle
    # copied and adopted from modular_example
    for car, car_battery, car_battery_controller in zip(
        my_cars, my_car_batteries, my_car_battery_controllers
    ):
        car_battery_controller.connect_only_predefined_connections(car)
        car_battery_controller.connect_only_predefined_connections(car_battery)
        car_battery.connect_only_predefined_connections(car_battery_controller)

        if my_config.surplus_control_car:
            my_electricity_controller.add_component_input_and_connect(
                source_component_class=car_battery_controller,
                source_component_output=car_battery_controller.BatteryChargingPowerToEMS,
                source_load_type=lt.LoadTypes.ELECTRICITY,
                source_unit=lt.Units.WATT,
                source_tags=[
                    lt.ComponentType.CAR_BATTERY,
                    lt.InandOutputType.ELECTRICITY_REAL,
                ],
                # source_weight=car_battery.source_weight,
                source_weight=1,
            )

            electricity_target = my_electricity_controller.add_component_output(
                source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
                source_tags=[
                    lt.ComponentType.CAR_BATTERY,
                    lt.InandOutputType.ELECTRICITY_TARGET,
                ],
                # source_weight=car_battery_controller.source_weight,
                source_weight=1,
                source_load_type=lt.LoadTypes.ELECTRICITY,
                source_unit=lt.Units.WATT,
                output_description="Target Electricity for EV Battery Controller. ",
            )

            car_battery_controller.connect_dynamic_input(
                input_fieldname=controller_l1_generic_ev_charge.L1Controller.ElectricityTarget,
                src_object=electricity_target,
            )
        else:
            my_electricity_controller.add_component_input_and_connect(
                source_component_class=car_battery_controller,
                source_component_output=car_battery_controller.BatteryChargingPowerToEMS,
                source_load_type=lt.LoadTypes.ELECTRICITY,
                source_unit=lt.Units.WATT,
                source_tags=[
                    lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED,
                ],
                source_weight=999,
            )

    # -----------------------------------------------------------------------------------------------------------------
    # connect EMS
    # copied and adopted from household_with_advanced_hp_hws_hds_pv_battery_ems
    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_occupancy,
        source_component_output=my_occupancy.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
        source_weight=999,
    )

    # connect EMS with DHW
    if clever:
        my_domnestic_hot_water_heatpump_controller.connect_input(
            my_domnestic_hot_water_heatpump_controller.StorageTemperatureModifier,
            my_electricity_controller.component_name,
            my_electricity_controller.StorageTemperatureModifier,
        )
        my_electricity_controller.add_component_input_and_connect(
            source_component_class=my_domnestic_hot_water_heatpump,
            source_component_output=my_domnestic_hot_water_heatpump.ElectricityOutput,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            source_tags=[
                lt.ComponentType.HEAT_PUMP_DHW,
                lt.InandOutputType.ELECTRICITY_REAL,
            ],
            # source_weight=my_dhw_heatpump_config.source_weight,
            source_weight=2,
        )

        my_electricity_controller.add_component_output(
            source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
            source_tags=[
                lt.ComponentType.HEAT_PUMP_DHW,
                lt.InandOutputType.ELECTRICITY_TARGET,
            ],
            # source_weight=my_domnestic_hot_water_heatpump.config.source_weight,
            source_weight=2,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            output_description="Target electricity for dhw heat pump.",
        )

    else:
        my_electricity_controller.add_component_input_and_connect(
            source_component_class=my_domnestic_hot_water_heatpump,
            source_component_output=my_domnestic_hot_water_heatpump.ElectricityOutput,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
            source_weight=999,
        )

    # connect EMS with Heatpump
    if clever:
        my_heat_pump_controller.connect_input(
            my_heat_pump_controller.SimpleHotWaterStorageTemperatureModifier,
            my_electricity_controller.component_name,
            my_electricity_controller.SimpleHotWaterStorageTemperatureModifier,
        )

        my_electricity_controller.add_component_input_and_connect(
            source_component_class=my_heat_pump,
            source_component_output=my_heat_pump.ElectricalInputPower,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            source_tags=[
                lt.ComponentType.HEAT_PUMP_BUILDING,
                lt.InandOutputType.ELECTRICITY_REAL,
            ],
            source_weight=3,
        )

        my_electricity_controller.add_component_output(
            source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
            source_tags=[
                lt.ComponentType.HEAT_PUMP_BUILDING,
                lt.InandOutputType.ELECTRICITY_TARGET,
            ],
            source_weight=3,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            output_description="Target electricity for Heat Pump. ",
        )

    else:
        my_electricity_controller.add_component_input_and_connect(
            source_component_class=my_heat_pump,
            source_component_output=my_heat_pump.ElectricalInputPower,
            source_load_type=lt.LoadTypes.ELECTRICITY,
            source_unit=lt.Units.WATT,
            source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
            source_weight=999,
        )

    # connect EMS BuildingTemperatureModifier with set_heating_temperature_for_building_in_celsius
    if my_config.surplus_control_building_temperature_modifier:
        my_heat_distribution_controller.connect_input(
            my_heat_distribution_controller.BuildingTemperatureModifier,
            my_electricity_controller.component_name,
            my_electricity_controller.BuildingTemperatureModifier,
        )
        my_building.connect_input(
            my_building.BuildingTemperatureModifier,
            my_electricity_controller.component_name,
            my_electricity_controller.BuildingTemperatureModifier,
        )

    # connect EMS with PV
    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_photovoltaic_system,
        source_component_output=my_photovoltaic_system.ElectricityOutput,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.InandOutputType.ELECTRICITY_PRODUCTION],
        source_weight=999,
    )

    # connect EMS with Battery
    my_electricity_controller.add_component_input_and_connect(
        source_component_class=my_advanced_battery,
        source_component_output=my_advanced_battery.AcBatteryPower,
        source_load_type=lt.LoadTypes.ELECTRICITY,
        source_unit=lt.Units.WATT,
        source_tags=[lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_REAL],
        source_weight=4,
    )

    electricity_to_or_from_battery_target = (
        my_electricity_controller.add_component_output(
            source_output_name=lt.InandOutputType.ELECTRICITY_TARGET,
            source_tags=[
                lt.ComponentType.BATTERY,
                lt.InandOutputType.ELECTRICITY_TARGET,
            ],
            source_weight=4,
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
    # connect Electricity Meter
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
    my_sim.add_component(my_heat_pump)
    my_sim.add_component(my_heat_pump_controller)
    my_sim.add_component(my_heat_distribution)
    my_sim.add_component(my_heat_distribution_controller)
    my_sim.add_component(my_simple_hot_water_storage)
    my_sim.add_component(my_domnestic_hot_water_storage)
    my_sim.add_component(my_domnestic_hot_water_heatpump_controller)
    my_sim.add_component(my_domnestic_hot_water_heatpump)
    my_sim.add_component(my_electricity_meter)
    my_sim.add_component(my_advanced_battery)
    my_sim.add_component(my_electricity_controller)
    for car in my_cars:
        my_sim.add_component(car)
    for car_battery in my_car_batteries:
        my_sim.add_component(car_battery)
    for car_battery_controller in my_car_battery_controllers:
        my_sim.add_component(car_battery_controller)
