from dataclasses import dataclass, field
from math import ceil
from typing import List, Optional, cast
from qiskit import QuantumCircuit
from qiskit.circuit import Delay
from encryption_circuit import encrypt
from experiment import Experiment
from qiskit.providers.ibmq.managed import ManagedResults
from collections import Counter
from experiment_properties import ExperimentProperties
from scheme_parameters import SchemeParameters
from states import Key
from utils import random_bit_string


@dataclass
class ExperimentManager:
    experiments: List[Experiment] = field(init=False, default_factory=list)
    transpiled_circuits: List[QuantumCircuit] = field(
        init=False, default_factory=list)

    def collect_circuits(self) -> List[QuantumCircuit]:
        collected_circuits = []
        for experiment in self.experiments:
            for circuit_list in experiment.full_circuits:
                collected_circuits.extend(circuit_list)
        return collected_circuits

    def save_transpiled_circuits(self, transpiled_circuits: List[QuantumCircuit]) -> None:
        circuit_index = 0
        for experiment in self.experiments:
            experiment.transpiled_circuits = []
            for _ in range(3):
                experiment.transpiled_circuits.append(
                    transpiled_circuits[circuit_index:circuit_index + experiment.number_of_circuits])
                circuit_index += experiment.number_of_circuits

    def process_results(self, results: ManagedResults) -> None:
        circuit_index = 0
        for experiment in self.experiments:
            experiment.deletion_counts_test1 = self.process_counts(experiment.experiment_properties.shots, cast(List[List[str]], [
                results.get_memory(i) for i in range(circuit_index, circuit_index + experiment.number_of_circuits)]))
            experiment.combined_counts_test3 = experiment.deletion_counts_test1
            circuit_index += experiment.number_of_circuits

            experiment.decryption_counts_test2 = self.process_counts(experiment.experiment_properties.shots, cast(List[List[str]], [
                results.get_memory(i) for i in range(circuit_index, circuit_index + experiment.number_of_circuits)]))
            experiment.combined_counts_test5 = experiment.decryption_counts_test2
            circuit_index += experiment.number_of_circuits

            experiment.combined_counts_test4 = self.process_counts(experiment.experiment_properties.shots, cast(List[List[str]], [
                results.get_memory(i) for i in range(circuit_index, circuit_index + experiment.number_of_circuits)]))
            circuit_index += experiment.number_of_circuits

    def process_counts(self, shots: int, memory: List[List[str]]) -> Counter[str]:
        shot_list = []
        for shot in range(shots):
            shot_list.append("".join(circuit[shot][::-1]
                             for circuit in memory))
        return Counter(shot_list)

    def set_up_experiments(self, experiment_properties: ExperimentProperties | List[ExperimentProperties],  scheme_parameters: SchemeParameters, num_experiments: int, folder_prefix: str, base_id: str, base_experiment: Optional[Experiment] = None):
        if isinstance(experiment_properties, ExperimentProperties):
            experiment_properties = [experiment_properties] * num_experiments

        for i, specific_exp_properties in enumerate(experiment_properties):
            if base_experiment:
                scheme_parameters = base_experiment.scheme_parameters
                key = base_experiment.key
                message = base_experiment.message
                ciphertext = base_experiment.ciphertext
                for circuit in ciphertext.circuits:
                    circuit.data = [instruction for instruction in circuit.data if not isinstance(
                        instruction[0], Delay)]
                    if specific_exp_properties.microsecond_delay > 0:
                        circuit.delay(specific_exp_properties.microsecond_delay, range(
                            circuit.num_qubits), unit="us")
            else:
                # Create new states
                key = Key.generate_key(scheme_parameters)
                message = random_bit_string(scheme_parameters.n)
                ciphertext = encrypt(
                    message, key, scheme_parameters, specific_exp_properties.qubits_per_circuit)
                if specific_exp_properties.qubits_per_circuit > 0:
                    for circuit in ciphertext.circuits:
                        circuit.delay(specific_exp_properties.microsecond_delay, range(
                            circuit.num_qubits), unit="us")
            experiment_id = f"{base_id}-{i}"
            specific_exp_properties.experiment_id = experiment_id

            self.experiments.append(Experiment(
                experiment_id=experiment_id,
                folder_path=f"{folder_prefix}/{experiment_id}",
                experiment_properties=specific_exp_properties,
                number_of_circuits=ceil(
                    scheme_parameters.m / specific_exp_properties.qubits_per_circuit),
                scheme_parameters=scheme_parameters,
                key=key,
                ciphertext=ciphertext,
                message=message,
                base_circuits=[circuit.copy()
                               for circuit in ciphertext.circuits]
            ))
