""" Class for the simulation repository. """
# clean
from typing import Any, Dict
from threading import Lock
import enum
from hisim import loadtypes as lt


# https://refactoring.guru/design-patterns/singleton/python/example#example-1


class SingletonMeta(type):

    """A class for a thread-safe implementation of Singleton."""

    _instances: Dict[Any, Any] = {}

    _lock: Lock = Lock()
    # We now have a lock object that will be used to synchronize threads during first access to the Singleton.

    def __call__(cls, *args, **kwargs):
        """Possible changes to the value of the `__init__` argument do not affect the returned instance."""
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class SingletonSimRepository(metaclass=SingletonMeta):

    """Class for exchanging information across all components."""

    def __init__(self) -> None:
        """Initializes the SimRepository."""
        self.my_dict: Dict[Any, Any] = {}
        self.my_dynamic_dict: Dict[lt.ComponentType, Dict[int, Any]] = {
            elem: {} for elem in lt.ComponentType
        }

    def set_entry(self, key: Any, entry: Any) -> None:
        """Sets an entry in the SimRepository."""
        self.my_dict[key] = entry

    def get_entry(self, key: Any) -> Any:
        """Gets an entry from the SimRepository."""
        return self.my_dict[key]

    def exist_entry(self, key: Any) -> bool:
        """Checks if an entry exists."""
        if key in self.my_dict:
            return True
        return False

    def delete_entry(self, key: Any) -> None:
        """Deletes an existing entry."""
        self.my_dict.pop(key)

    def set_dynamic_entry(
        self, component_type: lt.ComponentType, source_weight: int, entry: Any
    ) -> None:
        """Sets a dynamic entry."""
        self.my_dynamic_dict[component_type][source_weight] = entry

    def get_dynamic_entry(
        self, component_type: lt.ComponentType, source_weight: int
    ) -> Any:
        """Gets a dynmaic entry."""
        component = self.my_dynamic_dict.get(component_type, None)
        if component is None:
            return None
        value = component.get(source_weight, None)
        return value

    def get_dynamic_component_weights(self, component_type: lt.ComponentType) -> list:
        """Gets weights for dynamic components."""
        return list(self.my_dynamic_dict[component_type].keys())

    def delete_dynamic_entry(
        self, component_type: lt.ComponentType, source_weight: int
    ) -> Any:
        """Deletes a dynamic component entry."""
        self.my_dynamic_dict[component_type].pop(source_weight)

    def clear(self):
        """Clears all dictionaries at the end of the simulation to enable garbage collection and reduce memory consumption."""
        self.my_dict.clear()
        del self.my_dict
        self.my_dynamic_dict.clear()
        del self.my_dynamic_dict


class SingletonDictKeyEnum(enum.Enum):

    """Class for setting dictionary keys in the singleton sim repository."""

    SETHEATINGTEMPERATUREFORBUILDING = 1
    SETCOOLINGTEMPERATUREFORBUILDING = 2
    WATERMASSFLOWRATEOFHEATINGDISTRIBUTIONSYSTEM = 3
    WATERMASSFLOWRATEOFHEATGENERATOR = 4
    SETHEATINGTEMPERATUREFORWATERSTORAGE = 5
    SETCOOLINGTEMPERATUREFORWATERSTORAGE = 6
    HEATINGSYSTEM = 7
    LOCATION = 8
    RESULT_SCENARIO_NAME = 9
    Thermal_transmission_coefficient_glazing = 19
    Thermal_transmission_Surface_IndoorAir = 11
    Thermal_transmission_coefficient_opaque_em = 12
    Thermal_transmission_coefficient_opaque_ms = 13
    Thermal_transmission_coefficient_ventillation = 14
    Thermal_capacity_envelope = 15
