#!/usr/bin/env python3
"""Quick test to verify timer decorator exception handling works."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.time.timer import timer_decorator

# Test sync function with exception
@timer_decorator
def failing_sync_function():
    raise ValueError("Test error")

# Test async function with exception
@timer_decorator
async def failing_async_function():
    raise RuntimeError("Async test error")

if __name__ == "__main__":
    print("Testing sync function exception handling...")
    try:
        failing_sync_function()
    except ValueError as e:
        print(f"Caught expected exception: {e}")
        print("Timer should have logged timing info above.")
    
    print("\nTesting async function exception handling...")
    import asyncio
    async def test_async():
        try:
            await failing_async_function()
        except RuntimeError as e:
            print(f"Caught expected exception: {e}")
            print("Timer should have logged timing info above.")
    
    asyncio.run(test_async())
    print("\nTest completed!")
