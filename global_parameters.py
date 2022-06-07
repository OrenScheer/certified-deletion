class GlobalParameters:
    def __init__(self, security_parameter_lambda):
        self.security_parameter_lambda = security_parameter_lambda
        self.n = self.calculate_n()
        self.m = self.calculate_m()
        self.k = self.calculate_k()
        self.s = self.calculate_s()
        self.tau = self.calculate_tau()
        self.mu = self.calculate_mu()

    # TODO: implement the below functions, according to the security parameter lambda.

    def calculate_n(self):
        """Returns the length of the message."""
        return 6

    def calculate_m(self):
        """Returns the total number of qubits."""
        return 15

    def calculate_k(self):
        """Returns the number of qubits used for deletion."""
        return 7

    def calculate_s(self):
        """Returns the number of qubits used as a one-time pad for encryption."""
        return self.m - self.k

    def calculate_tau(self):
        """Returns the length of the error correction hash."""
        return 5

    def calculate_mu(self):
        """Returns the length of the error syndromes."""
        return 5
