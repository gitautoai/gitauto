import subprocess
import sys
subprocess.run([sys.executable, "-m", "pytest", "services/github/check_suites/test_get_circleci_workflow_id.py::test_get_circleci_workflow_ids_http_error_exception", "-v"], check=True)