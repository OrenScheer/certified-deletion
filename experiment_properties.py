from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExperimentProperties:
    execution_datetime: datetime
    shots: int
    system: str
    microsecond_delay: int
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
        """Returns a SchemeParameters object based on the encoded JSON string."""
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
