# Contributing to the Project

## Running Tests Locally

To ensure code quality and functionality, we use `pytest` as our testing framework. Follow these steps to run tests locally:

1. **Install Dependencies**: Ensure all dependencies are installed. If `requirements.txt` is available, run:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Tests**: Execute the tests using `pytest`:
   ```bash
   pytest
   ```
3. **Check Test Coverage**: Optionally, check the test coverage using:
   ```bash
   pytest --cov=your_package_name
   ```

Ensure all tests pass before submitting a pull request.