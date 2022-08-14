"""The properties of a specific experiment on a quantum backend."""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExperimentProperties:
    """A set of properties for a specific experiment.

    Attributes:
        execution_datetime: The approximate time at which the experiment was run on a backend.
        shots: The number of times each test was run on the backend.
        system: A string representing which backend system was used.
        microsecond_delay: The time, in microseconds, between the preparation of the qubits and the first measurement.
        optimization_level: The optimization level chosen to run the circuits on the backend.
        qubits_per_circuit: The number of qubits prepared in each circuit to be run on the backend.
        experiment_id: A unique string to reference this experiment.
    """
    execution_datetime: datetime
    shots: int
    system: str
    microsecond_delay: float
    optimization_level: int
    qubits_per_circuit: int
    experiment_id: str = ""

    def to_json(self) -> str:
        """Returns a JSON string representing this object."""
        dictionary = vars(self).copy()
        dictionary["execution_datetime"] = dictionary["execution_datetime"].isoformat()
        return json.dumps(dictionary)

    @classmethod
    def from_json(cls, json_string: str) -> ExperimentProperties:
        """Returns an ExperimentProperties object based on the encoded JSON string."""
        dictionary = json.loads(json_string)
        return cls(
            experiment_id=dictionary["experiment_id"],
            execution_datetime=datetime.fromisoformat(
                dictionary["execution_datetime"]),
            shots=dictionary["shots"],
            system=dictionary["system"],
            microsecond_delay=dictionary["microsecond_delay"],
            optimization_level=dictionary["optimization_level"],
            qubits_per_circuit=dictionary["qubits_per_circuit"],
        )
