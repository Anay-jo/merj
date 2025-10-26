
"""Sample module for chunking demonstration."""

import math
import json
from typing import List, Dict

# Configuration
DEBUG = True
API_KEY = "secret"

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.history = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

def fibonacci(n: int) -> List[int]:
    """Generate Fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def process_data(data: Dict) -> Dict:
    """Process input data."""
    return {
        "processed": True,
        "count": len(data),
        "keys": list(data.keys())
    }

# Main execution
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(fibonacci(10))
