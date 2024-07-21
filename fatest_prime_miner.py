import threading
from multiprocessing import Process, Event
import time
import os
import base64
import hashlib
from math import isqrt, log2
from colorama import Fore, Style, init
import getpass
from concurrent.futures import ThreadPoolExecutor

# Initialize colorama
init(autoreset=True)

class MerkleTree:
    def __init__(self, data):
        self.leaves = [hashlib.sha256(str(item).encode()).hexdigest() for item in data]
        self.tree = []
        self.build_merkle_tree(self.leaves)

    def build_merkle_tree(self, leaves):
        def hash_pair(left, right):
            combined = left + right
            return hashlib.sha256(combined.encode()).hexdigest()

        level_count = int(log2(len(leaves))) + 1
        num_levels = level_count
        current_level = leaves
        self.tree = [current_level]

        while len(current_level) > 1:
            new_level = []
            with ThreadPoolExecutor() as executor:
                futures = []
                for i in range(0, len(current_level), 2):
                    left = current_level[i]
                    right = current_level[i + 1] if i + 1 < len(current_level) else left
                    futures.append(executor.submit(hash_pair, left, right))
                
                for future in futures:
                    new_level.append(future.result())

            self.tree.append(new_level)
            current_level = new_level

            # Display progress
            progress = (len(self.tree) - 1) / num_levels * 100
            print(f"Building Merkle Tree: {int(progress)}% done", end='\r')

    def get_merkle_root(self):
        return self.tree[-1][0] if self.tree else None

class PrimeMiner:
    def __init__(self):
        self.primes_list = []
        self.primes_found = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition()
        self.mining_paused = False
        self.stop_event = Event()
        self.process = None
        self.load_primes()
        self.start_mining()

    def sieve_of_eratosthenes(self, start, limit):
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, isqrt(limit) + 1):
            if sieve[i]:
                for multiple in range(i*i, limit + 1, i):
                    sieve[multiple] = False
        return [num for num, is_prime in enumerate(sieve) if is_prime and num >= start]

    def mine_primes(self):
        start = self.primes_list[-1] + 1 if self.primes_list else 1
        limit = start + 150000
        while not self.stop_event.is_set():
            with self.condition:
                while self.mining_paused:
                    self.condition.wait()
            
            new_primes = self.sieve_of_eratosthenes(start, limit)
            with self.lock:
                self.primes_list.extend(new_primes)
                self.primes_found += len(new_primes)
                self.save_primes(new_primes)  # Save all new primes immediately
            start = limit + 1
            limit += 150000
            time.sleep(5)

    def save_primes(self, primes):
        try:
            with open('primes.csv', 'r') as file:
                all_primes = file.read().strip().split(',')
        except FileNotFoundError:
            all_primes = []

        all_primes.extend(map(str, primes))
        with open('primes.csv', 'w') as file:
            file.write(','.join(all_primes))

    def load_primes(self):
        if os.path.exists('primes.csv'):
            with open('primes.csv', 'r') as file:
                all_primes = file.read().strip()
                if all_primes:  # Ensure the file is not empty
                    self.primes_list = list(map(int, all_primes.split(',')))
                    self.primes_found = len(self.primes_list)
                else:
                    self.primes_list = []
                    self.primes_found = 0
        else:
            self.primes_list = []
            self.primes_found = 0

    def start_mining(self):
        if self.process is not None:
            self.process.terminate()
            self.process.join()
        self.stop_event.clear()
        self.process = Process(target=self.mine_primes)
        self.process.start()

    def stop_mining(self):
        print(Fore.YELLOW + "Stopping the miner...")
        self.stop_event.set()
        if self.process is not None:
            self.process.terminate()
            self.process.join()

    def get_most_recent_prime(self):
        if self.primes_list:
            return self.primes_list[-1]
        return None

    def generate_shareable_string(self, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            with self.lock:  # Ensure thread-safe access
                # Stop mining
                print(Fore.YELLOW + "Stopping the miner to generate shareable string...")
                self.stop_mining()

                # Generate the Merkle root of the last 50 primes
                print(Fore.YELLOW + "Generating Merkle root...")
                last_50_primes = self.primes_list[-50:]
                merkle_tree = MerkleTree(last_50_primes)
                merkle_root = merkle_tree.get_merkle_root()

                shareable_string = f"{self.primes_found}:{merkle_root}"
                encoded_string = base64.b64encode(shareable_string.encode()).decode()

                # Resume mining
                print(Fore.YELLOW + "Resuming mining...")
                self.start_mining()

                # Validate shareable string
                if self.verify_shareable_string(encoded_string):
                    return encoded_string
                else:
                    print(Fore.RED + "Shareable string validation failed, retrying...")
                    attempt += 1

        print(Fore.RED + "Failed to generate a valid shareable string after multiple attempts.")
        return None

    def parse_shareable_string(self, encoded_string):
        try:
            decoded_string = base64.b64decode(encoded_string).decode()
            parts = decoded_string.split(':')
            if len(parts) == 2:
                primes_found, merkle_root = parts
                return int(primes_found), merkle_root
            return None, None
        except Exception as e:
            print(Fore.RED + f"Error parsing shareable string: {e}")
            return None, None

    def verify_shareable_string(self, encoded_string):
        try:
            primes_found, merkle_root = self.parse_shareable_string(encoded_string)
            if primes_found is None:
                return False

            # Verify the Merkle root for the last 50 primes
            last_50_primes = self.primes_list[primes_found-50:primes_found]
            merkle_tree = MerkleTree(last_50_primes)
            calculated_merkle_root = merkle_tree.get_merkle_root()
            if calculated_merkle_root != merkle_root:
                print(Fore.RED + f"Merkle root mismatch. Expected: {merkle_root}, Calculated: {calculated_merkle_root}")
                return False

            return True
        except Exception as e:
            print(Fore.RED + f"Error verifying shareable string: {e}")
            return False

    def clear_screen(self):
        # Clear the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_stats(self):
        self.clear_screen()
        print(Fore.GREEN + f"Primes Found: {self.primes_found}")
        most_recent_prime = self.get_most_recent_prime()
        if (most_recent_prime is not None):
            print(Fore.GREEN + f"Most Recent Prime: {most_recent_prime}")
        else:
            print(Fore.RED + "Most Recent Prime: None")

    def print_menu(self):
        print(Fore.CYAN + "\nMenu:")
        print(Fore.CYAN + "1. Display Stats")
        print(Fore.CYAN + "2. Share Chain")
        print(Fore.CYAN + "3. Load and Verify Chain")
        print(Fore.CYAN + "4. Exit")
        print(Style.RESET_ALL)

    def run(self):
        while True:
            self.display_stats()
            self.print_menu()
            choice = input(Fore.YELLOW + "Choose an option: ").strip()

            if choice == "1":
                self.display_stats()
            elif choice == "2":
                shareable_string = self.generate_shareable_string()
                if shareable_string:
                    print(Fore.GREEN + f"Shareable String: {shareable_string}")
                else:
                    print(Fore.RED + "Error generating shareable string.")
                getpass.getpass(prompt="Press Enter to continue...")
            elif choice == "3":
                encoded_string = input(Fore.YELLOW + "Paste the shareable string: ").strip()
                primes_found, merkle_root = self.parse_shareable_string(encoded_string)
                if primes_found and merkle_root:
                    print(Fore.GREEN + f"Primes Found: {primes_found}")
                    print(Fore.GREEN + f"Merkle Root: {merkle_root}")
                    if self.verify_shareable_string(encoded_string):
                        print(Fore.GREEN + "Chain is valid.")
                        print(Fore.GREEN + f"Primes Found: {primes_found}")
                        print(Fore.GREEN + f"Merkle Root: {merkle_root}")
                    else:
                        print(Fore.RED + "Chain verification failed.")
                else:
                    print(Fore.RED + "Error decoding or invalid shareable string.")
                getpass.getpass(prompt="Press Enter to continue...")

            elif choice == "4":
                print(Fore.GREEN + "Exiting...")
                self.stop_event.set()
                self.process.join()
                break
            else:
                print(Fore.RED + "Invalid option. Please try again.")
                print(Fore.YELLOW + "Press Enter to continue...", getpass.getpass())

if __name__ == "__main__":
    miner = PrimeMiner()
    try:
        miner.run()
    finally:
        print(Fore.YELLOW + "Shutting down the miner...")
        miner.stop_event.set()
        miner.process.join()
