class GlobalParameters:
    def __init__(self, security_parameter_lambda):
        self.security_parameter_lambda = security_parameter_lambda
        self.n = self.calculate_n()
        self.m = self.calculate_m()
        self.k = self.calculate_k()
        self.s = self.calculate_s()
        self.tau = self.calculate_tau()
        self.mu = self.calculate_mu()

    # TODO: implement the below functions

    def calculate_n(self):
        # Length of the message
        return 6

    def calculate_m(self):
        # Total number of qubits
        return 15

    def calculate_k(self):
        # Number of qubits used for deletion
        return 7

    def calculate_s(self):
        # Number of qubits used for a one-time pad for the message
        return self.m - self.k

    def calculate_tau(self):
        # Length of error correction hash
        return 5

    def calculate_mu(self):
        # Length of error syndromes
        return 5
