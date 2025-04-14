from cgi import print_environ

from Pyro4 import expose
import time
from datetime import timedelta


class Solver:
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        self.workers = workers if workers else []
        print("Initialized Solver")

    def solve(self):
        print("Job Started: Parallel Sieve of Eratosthenes")

        n = self.read_input()

        start = time.time()
        primes = self.parallel_sieve(n)
        duration = time.time() - start
        self.write_output(duration, primes)

        return primes

    def parallel_sieve(self, n):
        if n < 2:
            return []

        if len(self.workers) == 1:
            return self.sequential_sieve(n)

        sqrt_n = int(n ** 0.5) + 1
        base_primes = self.sequential_sieve(sqrt_n)

        step = (n - sqrt_n) // len(self.workers)
        mapped = []

        for i in range(len(self.workers)):
            low = sqrt_n + 1 + i * step
            high = sqrt_n + 1 + (i + 1) * step if i < len(self.workers) - 1 else n + 1
            mapped.append(self.workers[i].sieve_range(low, high, base_primes))

        print("Map phase completed.")

        reduced = Solver.myreduce(mapped)
        print("Reduce phase completed.")

        return sorted(base_primes + reduced)

    @staticmethod
    def myreduce(mapped):
        primes_parts = [result.value for result in mapped]
        return sum(primes_parts, [])

    @staticmethod
    @expose
    def sequential_sieve(n):
        sieve = [True] * (n + 1)
        sieve[0:2] = [False, False]
        for i in range(2, int(n ** 0.5) + 1):
            if sieve[i]:
                for j in range(i * i, n + 1, i):
                    sieve[j] = False
        return [i for i, is_prime in enumerate(sieve) if is_prime]

    @staticmethod
    @expose
    def sieve_range(low, high, base_primes):
        sieve = [True] * (high - low)
        for p in base_primes:
            start = max(p * p, ((low + p - 1) // p) * p)
            for j in range(start, high, p):
                sieve[j - low] = False
        return [i for i, is_prime in enumerate(sieve, start=low) if is_prime]

    def read_input(self):
        with open(self.input_file_name, 'r') as f:
            return int(f.read().strip())

    def write_output(self, execution_time, primes):
        formatted_time = str(timedelta(seconds=execution_time))
        with open(self.output_file_name, 'w') as f:
            f.write("Number of workers: " + str(len(self.workers)) + "\n")
            f.write("Execution Time: " + formatted_time + "\n")
            f.write("Number of primes: ")
            f.write(str(len(primes)) + "\n")
        print("Job Finished: Result written to output file.")