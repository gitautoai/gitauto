from dataclasses import dataclass

from services.claude.evaluate_quality_checks import evaluate_quality_checks
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger

QUALITY_GATE_MESSAGE = "Evaluate and improve test quality per coding standards."


@dataclass
class QualityGateResult:
    error: str = ""
    passed_count: int = 0


@handle_exceptions(default_return_value=QualityGateResult(), raise_on_error=False)
def run_quality_gate(clone_dir: str, impl_file: str, base_args: BaseArgs):
    """Return quality gate result with error (if failed) and passed check count."""
    test_file_paths = base_args.get("test_file_paths", []) or []
    logger.info("Running quality gate for %s", impl_file)

    source_content = read_local_file(file_path=impl_file, base_dir=clone_dir)
    if not source_content:
        logger.warning("Could not read source file %s for quality gate", impl_file)
        return QualityGateResult()

    test_files: list[tuple[str, str]] = []
    for tp in test_file_paths:
        content = read_local_file(file_path=tp, base_dir=clone_dir)
        if content and content.strip():
            test_files.append((tp, content))

    if not test_files:
        logger.info("No test files found for %s, quality gate passes", impl_file)
        return QualityGateResult()

    quality_results = evaluate_quality_checks(
        source_content=source_content,
        source_path=impl_file,
        test_files=test_files,
        model=base_args["model_id"],
    )
    if quality_results is None:
        logger.warning("Quality evaluation failed for %s, letting it pass", impl_file)
        return QualityGateResult()

    # Count total checks and find failures
    total_checks = 0
    failed_categories: list[str] = []
    failure_details: list[str] = []
    for category, checks in quality_results.items():
        for check_name, check_data in checks.items():
            total_checks += 1
            if check_data.get("status") == "fail":
                reason = check_data.get("reason", "")
                logger.info(
                    "Quality gate: %s.%s failed for %s: %s",
                    category,
                    check_name,
                    impl_file,
                    reason,
                )
                failed_categories.append(category)
                failure_details.append(f"{category}.{check_name}: {reason}")
                break

    if failed_categories:
        logger.warning(
            "Quality gate failed for %s: %d categories with failures: %s",
            impl_file,
            len(failed_categories),
            ", ".join(failed_categories),
        )
        details = "\n".join(failure_details)
        passed_count = total_checks - len(failed_categories)
        return QualityGateResult(
            error=f"Quality gate failed for {impl_file}:\n{details}",
            passed_count=passed_count,
        )

    logger.info("Quality gate passed for %s: all checks pass or N/A", impl_file)
    return QualityGateResult(passed_count=total_checks)
