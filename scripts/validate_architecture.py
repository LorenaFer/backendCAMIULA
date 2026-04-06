#!/usr/bin/env python3
"""CAMIULA Architecture Validator — static import analysis for Clean Architecture.

Validates that all modules follow the dependency rule:
  - domain/     → NO imports from application/, infrastructure/, presentation/, sqlalchemy
  - application/ → NO imports from infrastructure/, presentation/, sqlalchemy
  - presentation/routes/ → NO imports from infrastructure/ (except via dependencies.py)
  - presentation/dependencies.py → ONLY file in presentation/ allowed to import infrastructure/

Also checks structural completeness:
  - Every module has domain/, application/, infrastructure/, presentation/
  - Every module has presentation/dependencies.py

Usage:
    python scripts/validate_architecture.py              # Full scan
    python scripts/validate_architecture.py --git-diff HEAD~1  # Only changed files
    python scripts/validate_architecture.py --module patients  # Single module

Exit codes:
    0 = No violations
    1 = Violations found
"""

import argparse
import ast
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

# ── Configuration ────────────────────────────────────────────

MODULES_DIR = Path("app/modules")

# Cross-cutting modules allowed to import from other modules' infrastructure
CROSS_CUTTING_MODULES = {"dashboard", "reports"}

# Layers in canonical order
REQUIRED_LAYERS = ["domain", "application", "infrastructure", "presentation"]

REQUIRED_FILES = ["presentation/dependencies.py"]

# Forbidden imports by layer
FORBIDDEN_IMPORTS = {
    "domain": {
        "patterns": [
            "app.modules.{module}.application",
            "app.modules.{module}.infrastructure",
            "app.modules.{module}.presentation",
            "sqlalchemy",
        ],
        "description": "Domain must not import from other layers or SQLAlchemy",
    },
    "application": {
        "patterns": [
            "app.modules.{module}.infrastructure",
            "app.modules.{module}.presentation",
            "sqlalchemy",
        ],
        "description": "Application must not import from infrastructure/presentation or SQLAlchemy",
    },
    "presentation/routes": {
        "patterns": [
            "app.modules.{module}.infrastructure",
        ],
        "description": "Routes must not import directly from infrastructure (use dependencies.py)",
        "exempt_files": ["dependencies.py"],
    },
    "presentation": {
        "patterns": [
            "app.modules.{module}.infrastructure",
        ],
        "description": "Presentation must not import from infrastructure (except dependencies.py)",
        "exempt_files": ["dependencies.py"],
    },
}


@dataclass
class Violation:
    file: str
    line: int
    layer: str
    import_str: str
    rule: str
    severity: str = "VIOLATION"


@dataclass
class Exemption:
    file: str
    reason: str


@dataclass
class Report:
    violations: List[Violation] = field(default_factory=list)
    exemptions: List[Exemption] = field(default_factory=list)
    structural_issues: List[str] = field(default_factory=list)
    files_analyzed: int = 0
    modules_scanned: int = 0


def get_module_name(file_path: Path) -> Optional[str]:
    """Extract module name from file path."""
    parts = file_path.parts
    try:
        idx = parts.index("modules")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return None


def get_layer(file_path: Path, module_name: str) -> Optional[str]:
    """Determine which architectural layer a file belongs to."""
    rel = str(file_path)
    module_prefix = f"app/modules/{module_name}/"

    if module_prefix + "domain/" in rel:
        return "domain"
    if module_prefix + "application/" in rel:
        return "application"
    if module_prefix + "infrastructure/" in rel:
        return "infrastructure"
    if module_prefix + "presentation/routes/" in rel:
        return "presentation/routes"
    if module_prefix + "presentation/" in rel:
        return "presentation"
    return None


def extract_imports(file_path: Path) -> List[tuple]:
    """Parse a Python file and extract all import statements with line numbers."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.lineno, node.module))
    return imports


def check_file(file_path: Path, report: Report) -> None:
    """Check a single Python file for architecture violations."""
    module_name = get_module_name(file_path)
    if not module_name:
        return

    layer = get_layer(file_path, module_name)
    if not layer:
        return

    report.files_analyzed += 1
    imports = extract_imports(file_path)
    file_name = file_path.name

    # Check if this file is a dependencies.py (exempt from route rules)
    is_dependencies = file_name == "dependencies.py" and "presentation" in str(file_path)

    for line_no, import_str in imports:
        # Check each rule for this layer
        rules = FORBIDDEN_IMPORTS.get(layer, {})
        if not rules:
            continue

        patterns = rules.get("patterns", [])
        exempt_files = rules.get("exempt_files", [])

        # Skip if file is in exempt list
        if file_name in exempt_files:
            continue

        # Skip dependencies.py for route-level checks
        if is_dependencies and layer == "presentation/routes":
            continue

        for pattern in patterns:
            resolved = pattern.replace("{module}", module_name)

            if import_str.startswith(resolved):
                # Check cross-cutting exemption
                if module_name in CROSS_CUTTING_MODULES and "infrastructure" in resolved:
                    report.exemptions.append(Exemption(
                        file=f"{file_path}:{line_no}",
                        reason=f"Cross-cutting module '{module_name}' infra access (ADR-003)",
                    ))
                    continue

                report.violations.append(Violation(
                    file=str(file_path),
                    line=line_no,
                    layer=layer,
                    import_str=import_str,
                    rule=rules["description"],
                ))


def check_structure(report: Report, target_module: Optional[str] = None) -> None:
    """Check that all modules have the required directory structure."""
    if not MODULES_DIR.exists():
        report.structural_issues.append(f"Modules directory not found: {MODULES_DIR}")
        return

    modules = [target_module] if target_module else [
        d.name for d in MODULES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    for module in modules:
        module_path = MODULES_DIR / module
        if not module_path.exists():
            report.structural_issues.append(f"Module directory not found: {module_path}")
            continue

        report.modules_scanned += 1

        for layer in REQUIRED_LAYERS:
            layer_path = module_path / layer
            if not layer_path.exists():
                report.structural_issues.append(
                    f"[STRUCT] {module}/ missing {layer}/ directory"
                )

        for req_file in REQUIRED_FILES:
            file_path = module_path / req_file
            if not file_path.exists():
                report.structural_issues.append(
                    f"[STRUCT] {module}/ missing {req_file}"
                )


def get_git_changed_files(ref: str) -> Set[Path]:
    """Get files changed since a git ref."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True, text=True, check=True,
        )
        return {
            Path(f) for f in result.stdout.strip().split("\n")
            if f.endswith(".py") and f.startswith("app/modules/")
        }
    except subprocess.CalledProcessError:
        print(f"Warning: git diff failed for ref '{ref}'", file=sys.stderr)
        return set()


def collect_files(
    target_module: Optional[str] = None,
    git_ref: Optional[str] = None,
) -> List[Path]:
    """Collect Python files to analyze."""
    if git_ref:
        return [f for f in get_git_changed_files(git_ref) if f.exists()]

    base = MODULES_DIR / target_module if target_module else MODULES_DIR
    if not base.exists():
        return []

    return sorted(base.rglob("*.py"))


def print_report(report: Report) -> int:
    """Print the report and return exit code."""
    print("=" * 60)
    print("  CAMIULA Architecture Validator")
    print("=" * 60)
    print(f"Modules scanned: {report.modules_scanned}")
    print(f"Files analyzed:  {report.files_analyzed}")
    print()

    if report.structural_issues:
        print("STRUCTURAL ISSUES:")
        for issue in report.structural_issues:
            print(f"  {issue}")
        print()

    if report.violations:
        print(f"VIOLATIONS ({len(report.violations)}):")
        for v in report.violations:
            tag = f"V-{v.layer.upper().replace('/', '-')}"
            print(f"  [{tag}] {v.file}:{v.line}")
            print(f"         imports: {v.import_str}")
            print(f"         rule: {v.rule}")
            print()
    else:
        print("VIOLATIONS: None")
        print()

    if report.exemptions:
        print(f"EXEMPTIONS ({len(report.exemptions)}):")
        for e in report.exemptions:
            print(f"  [EXEMPT] {e.file}")
            print(f"           {e.reason}")
        print()

    total_issues = len(report.violations) + len(report.structural_issues)
    print("-" * 60)
    print(f"Summary: {len(report.violations)} violations, "
          f"{len(report.structural_issues)} structural issues, "
          f"{len(report.exemptions)} exemptions")

    if total_issues == 0:
        print("Status: PASS")
    else:
        print("Status: FAIL")

    print("=" * 60)
    return 1 if total_issues > 0 else 0


def main():
    parser = argparse.ArgumentParser(description="CAMIULA Architecture Validator")
    parser.add_argument(
        "--module", type=str, default=None,
        help="Scan a single module (e.g., patients)",
    )
    parser.add_argument(
        "--git-diff", type=str, default=None, metavar="REF",
        help="Only analyze files changed since REF (e.g., HEAD~1, main)",
    )
    args = parser.parse_args()

    report = Report()

    # Structural check
    check_structure(report, target_module=args.module)

    # Import analysis
    files = collect_files(target_module=args.module, git_ref=args.git_diff)
    for f in files:
        check_file(f, report)

    exit_code = print_report(report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
