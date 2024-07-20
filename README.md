# Prime Miner Terminal Application

This is a terminal-based application for mining prime numbers using the Sieve of Eratosthenes algorithm. The application allows users to mine primes, share their prime chain, and verify external prime chains. The application starts mining primes automatically upon startup, or if a `primes.csv` file is found, it loads from the last found prime and continues mining.

## Features

- Automatic mining of prime numbers upon startup.
- Load and continue mining from the last found prime if a `primes.csv` file is found.
- Display statistics such as the number of primes found and the most recent prime.
- Share your prime chain as a base64 encoded string.
- Load and verify external prime chains.
- Easy-to-use menu system.
- Error handling and terminal color formatting with `colorama`.

## Requirements

- Python 3.10+
- `colorama` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/prime-miner-terminal.git
    cd prime-miner-terminal
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the application:
    ```sh
    python app.py
    ```

2. Use the menu to navigate through the application.

## Menu Options

1. **Display Stats:** Shows the number of primes found and the most recent prime.
2. **Share Chain:** Generates a base64 encoded string of the chain information which can be shared with others.
3. **Load and Verify Chain:** Allows you to paste a base64 encoded string of an external chain to verify its legitimacy.
4. **Exit:** Exits the application.

## Example

### Display Stats

