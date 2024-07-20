import threading
import time
import os
import base64
import hashlib
from math import isqrt
from colorama import Fore, Style, init
import getpass

# Initialize colorama
init(autoreset=True)

class MerkleTree:
    def __init__(self, data):
        self.leaves = [hashlib.sha256(str(item).encode()).hexdigest() for item in data]
        self.tree = self.build_merkle_tree(self.leaves)

    def build_merkle_tree(self, leaves):
        if len(leaves) == 1:
            return leaves
        new_level = []
        for i in range(0, len(leaves), 2):
            left = leaves[i]
            right = leaves[i+1] if i + 1 < len(leaves) else leaves[i]
            combined = left + right
            new_level.append(hashlib.sha256(combined.encode()).hexdigest())
        return self.build_merkle_tree(new_level) + new_level

    def get_merkle_root(self):
        return self.tree[-1] if self.tree else None

class PrimeMiner:
    def __init__(self):
        self.primes_list = []
        self.primes_found = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
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
        self.mining_thread = threading.Thread(target=self.mine_primes)
        self.mining_thread.start()

    def get_most_recent_prime(self):
        try:
            with open('primes.csv', 'r') as file:
                all_primes = file.read().strip().split(',')
                if all_primes:
                    return int(all_primes[-1])
                return None
        except FileNotFoundError:
            return None

    def generate_shareable_string(self):
        most_recent_prime = self.get_most_recent_prime()
        if most_recent_prime is None:
            return None
        
        # Generate the Merkle root of primes.csv
        merkle_tree = MerkleTree(self.primes_list)
        merkle_root = merkle_tree.get_merkle_root()
        
        shareable_string = f"{most_recent_prime}:{self.primes_found}:{merkle_root}"
        encoded_string = base64.b64encode(shareable_string.encode()).decode()
        return encoded_string

    def parse_shareable_string(self, encoded_string):
        try:
            decoded_string = base64.b64decode(encoded_string).decode()
            parts = decoded_string.split(':')
            if len(parts) == 3:
                most_recent_prime, primes_found, merkle_root = parts
                return int(most_recent_prime), int(primes_found), merkle_root
            return None, None, None
        except Exception as e:
            print(Fore.RED + f"Error parsing shareable string: {e}")
            return None, None, None

    def verify_chain(self, external_most_recent_prime, external_primes_found, external_merkle_root):
        # Ensure the length of the chain to verify is less than or equal to our chain length
        if external_primes_found > self.primes_found:
            print(Fore.RED + "Provided chain length is longer than our chain.")
            return False
        
        # Ensure the last prime number matches
        if self.primes_list[external_primes_found - 1] != external_most_recent_prime:
            print(Fore.RED + "Most recent prime mismatch.")
            return False

        # Verify the Merkle root for the length of the provided chain
        partial_chain = self.primes_list[:external_primes_found]
        merkle_tree = MerkleTree(partial_chain)
        calculated_merkle_root = merkle_tree.get_merkle_root()
        if calculated_merkle_root != external_merkle_root:
            print(Fore.RED + "Merkle root mismatch.")
            return False

        return True

    def clear_screen(self):
        # Clear the terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_stats(self):
        self.clear_screen()
        print(Fore.GREEN + f"Primes Found: {self.primes_found}")
        most_recent_prime = self.get_most_recent_prime()
        if most_recent_prime is not None:
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
                most_recent_prime, primes_found, merkle_root = self.parse_shareable_string(encoded_string)
                if most_recent_prime is not None:
                    if self.verify_chain(most_recent_prime, primes_found, merkle_root):
                        print(Fore.GREEN + "Chain is valid.")
                        print(Fore.GREEN + f"Most Recent Prime: {most_recent_prime}")
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
                if hasattr(self, 'mining_thread'):
                    self.mining_thread.join()
                break
            else:
                print(Fore.RED + "Invalid option. Please try again.")
                print(Fore.YELLOW + "Press Enter to continue...", getpass.getpass())

if __name__ == "__main__":
    miner = PrimeMiner()
    miner.run()
