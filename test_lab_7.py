#!/usr/bin/env python3
"""
Autograding validation for Lab 7: PID Tuning and Control with Crazyflie.
Run with: pytest test_lab_7.py -v
"""

import ast
import os
import warnings

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
EXPECTED_PKG_PATTERNS = ["lab07", "crazyflie", "pid"]

# Starter template text that indicates the student hasn't updated the file
README_STARTER_FINGERPRINT = "Update this README with your name, NetID, and instructions"


def _find_ros2_package():
    """Find the ROS 2 package directory under ros2_ws/src/."""
    src_dir = os.path.join("ros2_ws", "src")
    if not os.path.isdir(src_dir):
        return None
    for entry in os.listdir(src_dir):
        entry_lower = entry.lower()
        if any(p in entry_lower for p in EXPECTED_PKG_PATTERNS):
            full = os.path.join(src_dir, entry)
            if os.path.isdir(full):
                return full
    # Fallback: first directory with package.xml
    for entry in os.listdir(src_dir):
        full = os.path.join(src_dir, entry)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "package.xml")):
            return full
    return None


def _find_python_files(pkg_dir):
    py_files = []
    for root, dirs, files in os.walk(pkg_dir):
        for f in files:
            if f.endswith(".py") and f not in ("setup.py", "__init__.py", "conftest.py"):
                py_files.append(os.path.join(root, f))
    return py_files


def _get_images(docs_dir="docs"):
    if not os.path.isdir(docs_dir):
        return []
    return [
        f for f in os.listdir(docs_dir)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]


def _check_syntax(path):
    with open(path, "r", errors="replace") as f:
        source = f.read()
    ast.parse(source, filename=path)


# ── Required files (hard fail) ──────────────────────────────


def test_readme_exists():
    assert os.path.isfile("README.md"), "README.md not found"


def test_readme_not_empty():
    assert os.path.getsize("README.md") > 0, "README.md is empty"


def test_readme_updated():
    with open("README.md", "r", errors="replace") as f:
        content = f.read()
    assert README_STARTER_FINGERPRINT not in content, (
        "README.md still contains the starter template text. "
        "Please update it with your name, NetID, and instructions for running your code."
    )


def test_docs_directory_exists():
    assert os.path.isdir("docs"), "docs/ directory not found"


def test_ros2_src_exists():
    assert os.path.isdir(os.path.join("ros2_ws", "src")), "ros2_ws/src/ not found"


def test_ros2_package_found():
    pkg = _find_ros2_package()
    assert pkg is not None, (
        "No ROS 2 package found under ros2_ws/src/ "
        "matching lab07/crazyflie/pid"
    )
    print(f"Found package: {os.path.basename(pkg)}")


def test_setup_py_exists():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    assert os.path.isfile(os.path.join(pkg, "setup.py")), "setup.py not found in package"


def test_package_xml_exists():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    assert os.path.isfile(os.path.join(pkg, "package.xml")), "package.xml not found in package"


def test_python_source_files_exist():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    py_files = _find_python_files(pkg)
    assert len(py_files) > 0, "No Python source files found in the package"
    print(f"Found {len(py_files)} source file(s):")
    for pf in sorted(py_files):
        print(f"  - {os.path.relpath(pf)}")


# ── Python syntax (hard fail) ───────────────────────────────


def test_all_python_syntax():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    for pf in _find_python_files(pkg):
        _check_syntax(pf)


# ── Screenshots (warnings) ──────────────────────────────────


def test_screenshot_count():
    images = _get_images()
    print(f"\nFound {len(images)} image(s) in docs/:")
    for img in sorted(images):
        print(f"  - {img}")
    if len(images) < 2:
        warnings.warn(f"Expected at least 2 screenshots, found {len(images)}")


# ── Git hygiene (warnings) ──────────────────────────────────


def test_gitignore_exists():
    if not os.path.isfile(".gitignore"):
        warnings.warn(".gitignore not found — build/, install/, log/ should be excluded")


def test_no_build_artifacts():
    for d in ["build", "install", "log"]:
        for base in [".", "ros2_ws"]:
            path = os.path.join(base, d)
            if os.path.isdir(path):
                warnings.warn(f"'{path}' is committed — should be in .gitignore")
