"""
Praxis stack detection module.

Analyzes a project directory to detect the technology stack, frameworks,
and dependencies. Phase 1 supports Python stack detection only.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StackInfo:
    """
    Information about a detected technology stack.
    
    Attributes:
        stack_name: "Python" or "Generic"
        frameworks: Detected framework display names (e.g., ["Flask", "pytest"])
        dependencies: Raw dependency names, lowercased and deduplicated
        python_files_count: Number of .py files found (excluding venv, etc.)
        has_requirements_txt: Whether requirements.txt exists
        has_pyproject_toml: Whether pyproject.toml exists
    """
    stack_name: str
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    python_files_count: int = 0
    has_requirements_txt: bool = False
    has_pyproject_toml: bool = False


# Framework detection mapping: dependency name substring -> display name
FRAMEWORK_MAPPING: dict[str, str] = {
    "flask": "Flask",
    "fastapi": "FastAPI",
    "django": "Django",
    "pandas": "pandas",
    "numpy": "numpy",
    "pytest": "pytest",
}

# Directories to ignore when counting Python files
IGNORE_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "praxis_output",
    "bob_sessions",
}


def _should_ignore_file(file_path: Path) -> bool:
    """
    Check if a file should be ignored based on its path components.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if the file is in an ignored directory
    """
    return any(part in IGNORE_DIRS for part in file_path.parts)


def _parse_requirements_txt(requirements_path: Path) -> list[str]:
    """
    Parse a requirements.txt file and extract dependency names.
    
    Strips version specifiers, comments, and whitespace. Returns lowercased
    dependency names.
    
    Args:
        requirements_path: Path to requirements.txt
        
    Returns:
        List of dependency names (lowercased, no versions)
    """
    dependencies = []
    
    try:
        # Try UTF-8 first, fall back to latin-1 if that fails
        try:
            with open(requirements_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(requirements_path, "r", encoding="latin-1") as f:
                lines = f.readlines()
        
        for line in lines:
                # Strip whitespace
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Strip inline comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                
                # Strip editable install prefix
                if line.startswith("-e "):
                    line = line[3:].strip()
                
                # Strip version specifiers
                for separator in ["==", ">=", "<=", ">", "<", "~=", "!=", "[", ";"]:
                    if separator in line:
                        line = line.split(separator)[0].strip()
                        break
                
                # Strip BOM if present and lowercase
                if line:
                    line = line.lstrip('\ufeff')
                    dependencies.append(line.lower())
    
    except (OSError, UnicodeDecodeError) as e:
        # If file can't be read, return empty list rather than failing
        print(f"Warning: Could not read {requirements_path}: {e}")
        return []
    
    return dependencies


def _parse_pyproject_toml(pyproject_path: Path) -> list[str]:
    """
    Parse a pyproject.toml file and extract dependency names.
    
    Extracts from both [project.dependencies] and [tool.poetry.dependencies].
    Strips version specifiers and returns lowercased names.
    
    Args:
        pyproject_path: Path to pyproject.toml
        
    Returns:
        List of dependency names (lowercased, no versions)
    """
    dependencies = []
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        # Extract from [project.dependencies] (PEP 621 format)
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep_string in project_deps:
            # Strip version specifiers (same as requirements.txt)
            for separator in ["==", ">=", "<=", ">", "<", "~=", "!=", "[", ";"]:
                if separator in dep_string:
                    dep_string = dep_string.split(separator)[0].strip()
                    break
            
            if dep_string:
                dependencies.append(dep_string.lower())
        
        # Extract from [tool.poetry.dependencies] (Poetry format)
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for dep_name in poetry_deps.keys():
            # Skip the "python" key (it's the Python version requirement)
            if dep_name.lower() != "python":
                dependencies.append(dep_name.lower())
    
    except (OSError, tomllib.TOMLDecodeError) as e:
        # If file can't be read or parsed, return empty list
        print(f"Warning: Could not read {pyproject_path}: {e}")
        return []
    
    return dependencies


def _detect_frameworks(dependencies: list[str]) -> list[str]:
    """
    Detect frameworks from a list of dependencies.
    
    Args:
        dependencies: List of dependency names (lowercased)
        
    Returns:
        List of detected framework display names (deduplicated)
    """
    frameworks = []
    
    for dep in dependencies:
        for key, display_name in FRAMEWORK_MAPPING.items():
            if key in dep:
                if display_name not in frameworks:
                    frameworks.append(display_name)
    
    return frameworks


def detect_stack(project_path: Path) -> StackInfo:
    """
    Detect the technology stack of a project directory.
    
    Phase 1 supports Python stack detection only. Analyzes:
    - Python files (*.py) excluding venv and other ignored directories
    - requirements.txt for dependencies
    - pyproject.toml for dependencies
    
    Args:
        project_path: Path to the project directory to analyze
        
    Returns:
        StackInfo object with detected stack information
        
    Raises:
        ValueError: If project_path doesn't exist or isn't a directory
    """
    if not project_path.exists():
        raise ValueError(f"Project path does not exist: {project_path}")
    
    if not project_path.is_dir():
        raise ValueError(f"Project path is not a directory: {project_path}")
    
    # Step 1: Count Python files
    python_files = [
        f for f in project_path.rglob("*.py")
        if not _should_ignore_file(f)
    ]
    python_files_count = len(python_files)
    
    # Step 2: Parse requirements.txt
    requirements_path = project_path / "requirements.txt"
    has_requirements_txt = requirements_path.exists()
    dependencies = []
    
    if has_requirements_txt:
        dependencies.extend(_parse_requirements_txt(requirements_path))
    
    # Step 3: Parse pyproject.toml
    pyproject_path = project_path / "pyproject.toml"
    has_pyproject_toml = pyproject_path.exists()
    
    if has_pyproject_toml:
        dependencies.extend(_parse_pyproject_toml(pyproject_path))
    
    # Deduplicate dependencies (case-insensitive)
    dependencies = list(dict.fromkeys(dependencies))
    
    # Step 4: Detect frameworks
    frameworks = _detect_frameworks(dependencies)
    
    # Step 5: Determine stack name
    if python_files_count > 0 or has_requirements_txt or has_pyproject_toml:
        stack_name = "Python"
    else:
        stack_name = "Generic"
    
    return StackInfo(
        stack_name=stack_name,
        frameworks=frameworks,
        dependencies=dependencies,
        python_files_count=python_files_count,
        has_requirements_txt=has_requirements_txt,
        has_pyproject_toml=has_pyproject_toml,
    )


if __name__ == "__main__":
    # Self-test: detect stack of the praxis project itself
    result = detect_stack(Path("."))
    print(f"Stack: {result.stack_name}")
    print(f"Python files: {result.python_files_count}")
    print(f"Has requirements.txt: {result.has_requirements_txt}")
    print(f"Has pyproject.toml: {result.has_pyproject_toml}")
    print(f"Dependencies: {result.dependencies}")
    print(f"Frameworks: {result.frameworks}")

# Made with Bob
