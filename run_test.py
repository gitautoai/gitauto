import subprocess
import sys

# Run the specific failing test
result = subprocess.run([sys.executable, '-m', 'pytest', 'utils/files/test_should_skip_ruby.py::test_complex_constant_expressions', '-v'], 
                       capture_output=True, text=True)