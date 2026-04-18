#!/usr/bin/env python3
"""CAMIULA Clean Architecture Validator

Enhanced validator that checks all Clean Architecture standards as defined in
docs/CLEAN_ARCHITECTURE_STANDARDS.md

Validates:
  - Layer dependency rules (domain → application → infrastructure → presentation)
  - File and directory naming conventions
  - Required file structure
  - Repository pattern implementation
  - Use case pattern implementation
  - Cross-module import restrictions

Usage:
    python scripts/validate_architecture.py              # Full scan
    python scripts/validate_architecture.py --git-diff HEAD~1  # Only changed files
    python scripts/validate_architecture.py --module patients  # Single module
    python scripts/validate_architecture.py --naming-only      # Only naming conventions

Exit codes:
    0 = No violations
    1 = Violations found
"""

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Dict

# ── Configuration ────────────────────────────────────────────

MODULES_DIR = Path("app/modules")

# Cross-cutting modules allowed to import from other modules' infrastructure
CROSS_CUTTING_MODULES = {"dashboard", "reports"}

# Known dependency violations accepted as technical debt (tracked, not blocking CI).
# Format: "filepath:line" — these produce warnings instead of failures.
KNOWN_VIOLATIONS = {
    "app/modules/auth/presentation/routes/user_routes.py:118",      # inline model for user+doctor creation
    "app/modules/auth/presentation/routes/user_routes.py:123",      # inline model for user+doctor creation
    "app/modules/auth/presentation/routes/auth_routes.py:20",       # RevokedTokenRepository — mover a LogoutUseCase + dependencies.py
    "app/modules/medical_records/presentation/routes/medical_records_router.py:162",  # inline MedicalOrderModel
    "app/modules/medical_records/presentation/routes/medical_records_router.py:210",  # inline MedicalOrderModel
    "app/modules/medical_records/presentation/routes/medical_records_router.py:205",  # inline MedicalOrderModel
}

# Known naming violations accepted as technical debt (legacy file names, tracked).
# Format: "relative/path/to/file.py"
KNOWN_NAMING_VIOLATIONS = {
    # auth — archivos renombrados antes de que existiera el estándar
    "app/modules/auth/domain/repositories/auth_provider.py",            # debería: auth_provider_repository.py
    "app/modules/auth/infrastructure/repositories/revoked_token_repository.py",  # debería: sqlalchemy_revoked_token_repository.py
    "app/modules/auth/presentation/routes/user_routes.py",              # debería: user_router.py
    "app/modules/auth/presentation/routes/auth_routes.py",              # debería: auth_router.py
    "app/modules/auth/presentation/schemas/auth_schema.py",             # debería: auth_schemas.py
    # doctors — readers de disponibilidad (no son repos clásicos pero siguen el patrón)
    "app/modules/doctors/domain/repositories/availability_reader.py",                  # debería: availability_reader_repository.py
    "app/modules/doctors/infrastructure/repositories/sqlalchemy_availability_reader.py",  # debería: sqlalchemy_availability_reader_repository.py
}

# Layers in canonical order
REQUIRED_LAYERS = ["domain", "application", "infrastructure", "presentation"]

# Required subdirectories for each layer
REQUIRED_SUBDIRS = {
    "domain": ["entities", "repositories"],
    "application": ["dtos", "use_cases"],
    "infrastructure": ["repositories"],
    "presentation": ["routes", "schemas"]
}

REQUIRED_FILES = [
    "router.py",
    "presentation/dependencies.py",
    "infrastructure/models.py"
]

# Required file patterns for each subdirectory
REQUIRED_FILE_PATTERNS = {
    "domain/entities": r"^[a-z]+(_[a-z]+)*\.py$",
    "domain/repositories": r"^[a-z]+(_[a-z]+)*_repository\.py$",
    "application/dtos": r"^[a-z]+(_[a-z]+)*_dto\.py$",
    "application/use_cases": r"^[a-z]+(_[a-z]+)*\.py$",
    "infrastructure/repositories": r"^sqlalchemy_[a-z]+(_[a-z]+)*_repository\.py$",
    "presentation/routes": r"^[a-z]+(_[a-z]+)*_router\.py$",
    "presentation/schemas": r"^[a-z]+(_[a-z]+)*_schemas\.py$"
}

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
class NamingViolation:
    file: str
    type: str  # 'file', 'class', 'directory'
    name: str
    expected_pattern: str
    rule: str


@dataclass
class PatternViolation:
    file: str
    type: str  # 'repository', 'use_case', 'entity'
    issue: str
    rule: str


@dataclass
class Exemption:
    file: str
    reason: str


@dataclass
class Report:
    violations: List[Violation] = field(default_factory=list)
    naming_violations: List[NamingViolation] = field(default_factory=list)
    pattern_violations: List[PatternViolation] = field(default_factory=list)
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

                violation_key = f"{file_path}:{line_no}"
                if violation_key in KNOWN_VIOLATIONS:
                    report.exemptions.append(Exemption(
                        file=violation_key,
                        reason=f"Known technical debt (tracked)",
                    ))
                else:
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

        # Cross-cutting modules (dashboard, reports) aggregate data from multiple modules
        # and intentionally skip the full layer structure — exempt from structural checks (ADR-003).
        if module in CROSS_CUTTING_MODULES:
            continue

        # Check required layers
        for layer in REQUIRED_LAYERS:
            layer_path = module_path / layer
            if not layer_path.exists():
                report.structural_issues.append(
                    f"[STRUCT] {module}/ missing {layer}/ directory"
                )
            else:
                # Check __init__.py in each layer
                init_file = layer_path / "__init__.py"
                if not init_file.exists():
                    report.structural_issues.append(
                        f"[STRUCT] {module}/ missing {layer}/__init__.py"
                    )
                
                # Check required subdirectories
                required_subdirs = REQUIRED_SUBDIRS.get(layer, [])
                for subdir in required_subdirs:
                    subdir_path = layer_path / subdir
                    if not subdir_path.exists():
                        report.structural_issues.append(
                            f"[STRUCT] {module}/ missing {layer}/{subdir}/ directory"
                        )
                    elif not (subdir_path / "__init__.py").exists():
                        report.structural_issues.append(
                            f"[STRUCT] {module}/ missing {layer}/{subdir}/__init__.py"
                        )

        # Check required files
        for req_file in REQUIRED_FILES:
            file_path = module_path / req_file
            if not file_path.exists():
                report.structural_issues.append(
                    f"[STRUCT] {module}/ missing {req_file}"
                )


def check_naming_conventions(report: Report, target_module: Optional[str] = None) -> None:
    """Check file and class naming conventions."""
    if not MODULES_DIR.exists():
        return

    modules = [target_module] if target_module else [
        d.name for d in MODULES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    for module in modules:
        module_path = MODULES_DIR / module
        if not module_path.exists():
            continue

        # Check file naming in specific directories
        for dir_pattern, file_pattern in REQUIRED_FILE_PATTERNS.items():
            full_path = module_path / dir_pattern
            if not full_path.exists():
                continue
                
            for py_file in full_path.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                    
                if not re.match(file_pattern, py_file.name):
                    try:
                        rel_path = str(py_file.relative_to(Path.cwd()))
                    except ValueError:
                        rel_path = str(py_file)

                    # Known legacy naming — register as exemption, not violation
                    if rel_path in KNOWN_NAMING_VIOLATIONS:
                        report.exemptions.append(Exemption(
                            file=rel_path,
                            reason="Known legacy naming (pre-standard, tracked as tech debt)",
                        ))
                    else:
                        report.naming_violations.append(NamingViolation(
                            file=rel_path,
                            type="file",
                            name=py_file.name,
                            expected_pattern=file_pattern,
                            rule=f"Files in {dir_pattern}/ must follow pattern {file_pattern}"
                        ))

        # Check class naming in entities
        entities_dir = module_path / "domain" / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.py"):
                if entity_file.name == "__init__.py":
                    continue
                check_entity_class_naming(report, entity_file)
        
        # Check repository interfaces have implementations
        check_repository_implementations(report, module, module_path)


def check_entity_class_naming(report: Report, entity_file: Path) -> None:
    """Check that entity classes use PascalCase."""
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][A-Za-z0-9]*$', node.name):
                    try:
                        rel_path = str(entity_file.relative_to(Path.cwd()))
                    except ValueError:
                        rel_path = str(entity_file)
                    report.naming_violations.append(NamingViolation(
                        file=rel_path,
                        type="class",
                        name=node.name,
                        expected_pattern="PascalCase",
                        rule="Entity classes must use PascalCase naming"
                    ))
    except Exception:
        pass


def check_repository_implementations(report: Report, module: str, module_path: Path) -> None:
    """Check that every repository interface has a corresponding implementation."""
    domain_repos_dir = module_path / "domain" / "repositories"
    infra_repos_dir = module_path / "infrastructure" / "repositories"
    
    if not domain_repos_dir.exists() or not infra_repos_dir.exists():
        return
        
    # Get domain repository interfaces
    domain_repos = set()
    for repo_file in domain_repos_dir.glob("*.py"):
        if repo_file.name == "__init__.py":
            continue
        if repo_file.name.endswith("_repository.py"):
            entity_name = repo_file.name[:-14]  # Remove "_repository.py"
            domain_repos.add(entity_name)
    
    # Check for corresponding implementations
    for entity_name in domain_repos:
        expected_impl = f"sqlalchemy_{entity_name}_repository.py"
        impl_file = infra_repos_dir / expected_impl
        if not impl_file.exists():
            report.pattern_violations.append(PatternViolation(
                file=str(domain_repos_dir / f"{entity_name}_repository.py"),
                type="repository",
                issue=f"Missing implementation: {expected_impl}",
                rule="Every repository interface must have an SQLAlchemy implementation"
            ))


def check_use_case_patterns(report: Report, target_module: Optional[str] = None) -> None:
    """Check use case pattern implementation."""
    if not MODULES_DIR.exists():
        return

    modules = [target_module] if target_module else [
        d.name for d in MODULES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    for module in modules:
        module_path = MODULES_DIR / module
        use_cases_dir = module_path / "application" / "use_cases"
        
        if not use_cases_dir.exists():
            continue
            
        for uc_file in use_cases_dir.glob("*.py"):
            if uc_file.name == "__init__.py":
                continue
            check_use_case_file(report, uc_file)


def check_use_case_file(report: Report, uc_file: Path) -> None:
    """Check individual use case file for proper structure."""
    try:
        with open(uc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Find classes in the file
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
                
                # Check if class has execute method
                has_execute = False
                has_init = False
                has_call = False
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        if item.name == "execute":
                            has_execute = True
                        elif item.name == "__init__":
                            has_init = True
                        elif item.name == "__call__":
                            has_call = True
                
                if not has_execute and not has_call:
                    try:
                        rel_path = str(uc_file.relative_to(Path.cwd()))
                    except ValueError:
                        rel_path = str(uc_file)
                    report.pattern_violations.append(PatternViolation(
                        file=rel_path,
                        type="use_case",
                        issue=f"Class '{node.name}' missing 'execute' or '__call__' method",
                        rule="Use case classes must have an 'execute' or '__call__' method"
                    ))
                    
                if not has_init:
                    try:
                        rel_path = str(uc_file.relative_to(Path.cwd()))
                    except ValueError:
                        rel_path = str(uc_file)
                    report.pattern_violations.append(PatternViolation(
                        file=rel_path,
                        type="use_case", 
                        issue=f"Class '{node.name}' missing '__init__' method",
                        rule="Use case classes should have dependency injection via __init__"
                    ))
        
        if not classes:
            try:
                rel_path = str(uc_file.relative_to(Path.cwd()))
            except ValueError:
                rel_path = str(uc_file)
            report.pattern_violations.append(PatternViolation(
                file=rel_path,
                type="use_case",
                issue="No use case classes found",
                rule="Use case files should contain at least one use case class"
            ))
            
    except Exception:
        pass


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
    print("  CAMIULA Clean Architecture Validator")
    print("=" * 60)
    print(f"Modules scanned: {report.modules_scanned}")
    print(f"Files analyzed:  {report.files_analyzed}")
    print()

    if report.structural_issues:
        print(f"STRUCTURAL ISSUES ({len(report.structural_issues)}):")
        for issue in report.structural_issues:
            print(f"  {issue}")
        print()

    if report.violations:
        print(f"DEPENDENCY VIOLATIONS ({len(report.violations)}):")
        for v in report.violations:
            tag = f"V-{v.layer.upper().replace('/', '-')}"
            print(f"  [{tag}] {v.file}:{v.line}")
            print(f"         imports: {v.import_str}")
            print(f"         rule: {v.rule}")
            print()
    
    if report.naming_violations:
        print(f"NAMING VIOLATIONS ({len(report.naming_violations)}):")
        for nv in report.naming_violations:
            print(f"  [NAME-{nv.type.upper()}] {nv.file}")
            print(f"         name: {nv.name}")
            print(f"         expected: {nv.expected_pattern}")
            print(f"         rule: {nv.rule}")
            print()
    
    if report.pattern_violations:
        print(f"PATTERN VIOLATIONS ({len(report.pattern_violations)}):")
        for pv in report.pattern_violations:
            print(f"  [PATTERN-{pv.type.upper()}] {pv.file}")
            print(f"         issue: {pv.issue}")
            print(f"         rule: {pv.rule}")
            print()

    if report.exemptions:
        print(f"EXEMPTIONS ({len(report.exemptions)}):")
        for e in report.exemptions:
            print(f"  [EXEMPT] {e.file}")
            print(f"           {e.reason}")
        print()
    
    if not any([report.violations, report.naming_violations, report.pattern_violations, report.structural_issues]):
        print("✅ ALL CHECKS PASSED")
        print()

    total_issues = (
        len(report.violations) + 
        len(report.naming_violations) + 
        len(report.pattern_violations) + 
        len(report.structural_issues)
    )
    
    print("-" * 60)
    print(f"Summary: {len(report.violations)} dependency violations, "
          f"{len(report.naming_violations)} naming violations, "
          f"{len(report.pattern_violations)} pattern violations, "
          f"{len(report.structural_issues)} structural issues, "
          f"{len(report.exemptions)} exemptions")

    if total_issues == 0:
        print("Status: ✅ PASS")
    else:
        print("Status: ❌ FAIL")

    print("=" * 60)
    return 1 if total_issues > 0 else 0


def main():
    parser = argparse.ArgumentParser(description="CAMIULA Clean Architecture Validator")
    parser.add_argument(
        "--module", type=str, default=None,
        help="Scan a single module (e.g., patients)",
    )
    parser.add_argument(
        "--git-diff", type=str, default=None, metavar="REF",
        help="Only analyze files changed since REF (e.g., HEAD~1, main)",
    )
    parser.add_argument(
        "--naming-only", action="store_true",
        help="Only check naming conventions and patterns, skip dependency analysis",
    )
    parser.add_argument(
        "--skip-naming", action="store_true",
        help="Skip naming and pattern checks, only analyze dependencies",
    )
    args = parser.parse_args()

    report = Report()

    # Always check structure
    check_structure(report, target_module=args.module)

    if not args.skip_naming:
        # Check naming conventions
        check_naming_conventions(report, target_module=args.module)
        
        # Check use case patterns
        check_use_case_patterns(report, target_module=args.module)

    if not args.naming_only:
        # Import dependency analysis
        files = collect_files(target_module=args.module, git_ref=args.git_diff)
        for f in files:
            check_file(f, report)

    exit_code = print_report(report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
