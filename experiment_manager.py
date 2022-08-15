"""A class representing a set of experiments that are run for data collection."""
from math import ceil
from typing import List, Optional, Union, cast
from qiskit import QuantumCircuit
from qiskit.circuit import Delay
from encryption_circuit import encrypt
from experiment import Experiment
from qiskit.providers.ibmq.managed import ManagedResults
from collections import Counter
from experiment_properties import ExperimentProperties
from scheme_parameters import SchemeParameters
from states import Key, Ciphertext
from utils import random_bit_string


class ExperimentManager:
    """A class to create and manage the execution of a set of experiments on a quantum backend.

    Attributes:
        experiments: A list of Experiments that are to be tested.
    """

    def __init__(self):
        self.experiments: List[Experiment] = []

    def collect_circuits(self) -> List[QuantumCircuit]:
        """Returns a list of all circuits that have to be transpiled and run, for this set of experiments."""
        collected_circuits = []
        for experiment in self.experiments:
            for circuit_list in experiment.full_circuits:
                collected_circuits.extend(circuit_list)
        return collected_circuits

    def save_transpiled_circuits(self, transpiled_circuits: List[QuantumCircuit]) -> None:
        """Saves the transpiled circuits passed as an argument in this set of experiments, for future serializing and saving."""
        circuit_index = 0
        for experiment in self.experiments:
            experiment.transpiled_circuits = []
            for _ in range(3):
                experiment.transpiled_circuits.append(
                    transpiled_circuits[circuit_index:circuit_index + experiment.number_of_circuits])
                circuit_index += experiment.number_of_circuits

    def process_results(self, results: ManagedResults) -> None:
        """Re-assembles and processes the raw measurements from the ManagedResults provided by an IBMQJobManager in the run notebook.

        Saves the counts of each test to each experiment.
        """
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

    def process_counts(self, shots: int, memory: List[List[str]]) -> "Counter[str]":
        """Returns the measurements, in the appropriate format, for a single test of an experiment.

        Args:
            shots: The number of times this test was run on the backend.
            memory: A list of lists of strings, where each outer list is the results of a single
                circuit, and each inner list is each shot of the execution of that circuit.

        Returns:
            A Counter, where each key is a single shot across all the circuits. This key
                is appropriately processed to be in the right format, i.e. zero-indexed from the
                left. Each shot is considered part of the same run across many circuits.
        """
        shot_list = []
        for shot in range(shots):
            shot_list.append("".join(circuit[shot][::-1]
                             for circuit in memory))
        return Counter(shot_list)

    def set_up_experiments(self, num_experiments: int, experiment_properties: Union[ExperimentProperties, List[ExperimentProperties]],  scheme_parameters: SchemeParameters, folder_prefix: str, base_id: str, base_experiment: Optional[Experiment] = None):
        """Creates the set of experiments that this object will manage.

        Args:
            num_experiments: The number of experiments this object will manage.
            experiment_properties: Either a single instance of ExperimentProperties, which will be used for all the
                experiments, or a list of ExperimentProperties, where each one corresponds to one experiment.
                This allows properties, such as the microsecond delay, to vary between experiments.
            scheme_parameters: The parameters for all the experiments.
            folder_prefix: The prefix of the folder where the results of all the experiments will be stored.
            base_id: A unique id defining this set of experiments. The id of each experiment will be this base id
                plus the index, starting from 0, of each experiment.
            base_experiment: An optional Experiment from which to base all these new experiments. If given,
                the scheme parameters, key, message, and ciphertext will all be used from this existing
                experiment. The ExperimentProperties for each experiment will still come from the arguments.
        """

        if isinstance(experiment_properties, ExperimentProperties):
            experiment_properties = [experiment_properties] * num_experiments

        for i, specific_exp_properties in enumerate(experiment_properties):
            if base_experiment:
                # Use existing states
                scheme_parameters = base_experiment.scheme_parameters
                key = base_experiment.key
                message = base_experiment.message
                encoded_in_qubits = base_experiment.encoded_in_qubits
                new_ciphertext_circuits = []
                for circuit in base_experiment.ciphertext.circuits:
                    # Remove any existing delay in case it is of a different length than the current properties
                    new_circuit = circuit.copy()
                    new_circuit.data = [instruction for instruction in new_circuit.data if not isinstance(
                        instruction[0], Delay)]
                    if specific_exp_properties.microsecond_delay > 0:
                        new_circuit.delay(specific_exp_properties.microsecond_delay, range(
                            new_circuit.num_qubits), unit="us")
                    new_ciphertext_circuits.append(new_circuit)
                ciphertext = Ciphertext(circuits=new_ciphertext_circuits, c=base_experiment.ciphertext.c,
                                        p=base_experiment.ciphertext.p, q=base_experiment.ciphertext.q)
            else:
                # Create new states
                key = Key.generate_key(scheme_parameters)
                message = random_bit_string(scheme_parameters.n)
                ciphertext, encoded_in_qubits = encrypt(
                    message, key, scheme_parameters, specific_exp_properties.qubits_per_circuit)
                if specific_exp_properties.microsecond_delay > 0:
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
                               for circuit in ciphertext.circuits],
                encoded_in_qubits=encoded_in_qubits,
            ))
