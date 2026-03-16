#!/usr/bin/env python3
"""
Autograding validation for Lab 7: PID Tuning and Control with Crazyflie.
Run with: pytest test_lab_7.py -v
"""

import ast
import os
import re
import warnings

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
EXPECTED_PKG_PATTERNS = ["lab07", "crazyflie", "pid"]

README_STARTER_FINGERPRINT = "Update this README with your name, NetID, and instructions"

# The 9 PID parameters students must declare
REQUIRED_PID_PARAMS = [
    "kp_x", "kd_x", "ki_x",
    "kp_y", "kd_y", "ki_y",
    "kp_z", "kd_z", "ki_z",
]

# Velocity saturation parameters
VELOCITY_PARAMS = ["max_v_x", "max_v_y", "max_v_z"]

# Expected entry points in setup.py
EXPECTED_ENTRY_POINTS = {"goal_3d_controller", "trajectory_publisher", "plotting"}

# Expected script files
EXPECTED_SCRIPTS = ["3d_goal_control.py", "trajectory_publisher.py", "plotting.py"]


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


def _find_file_in_package(name):
    """Search for a file anywhere in the package directory tree."""
    pkg = _find_ros2_package()
    if pkg is None:
        return None
    for root, dirs, files in os.walk(pkg):
        if name in files:
            return os.path.join(root, name)
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


def _read_source(path):
    if path is None or not os.path.isfile(path):
        return None, None
    with open(path, "r", errors="replace") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return source, None
    return source, tree


def _get_controller_source():
    """Find and read the main controller file (3d_goal_control.py)."""
    path = _find_file_in_package("3d_goal_control.py")
    if path is None:
        # Try alternate names
        for name in ["goal_control.py", "pid_controller.py", "controller.py"]:
            path = _find_file_in_package(name)
            if path:
                break
    return _read_source(path)


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


def test_controller_script_exists():
    path = _find_file_in_package("3d_goal_control.py")
    assert path is not None, (
        "3d_goal_control.py not found in package. "
        "This is the main PID controller node."
    )


def test_trajectory_publisher_exists():
    path = _find_file_in_package("trajectory_publisher.py")
    assert path is not None, "trajectory_publisher.py not found in package"


def test_plotting_script_exists():
    path = _find_file_in_package("plotting.py")
    assert path is not None, "plotting.py not found in package"


# ── Python syntax (hard fail) ───────────────────────────────


def test_all_python_syntax():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    for pf in _find_python_files(pkg):
        _check_syntax(pf)


# ── PID parameter declarations (hard fail) ──────────────────


def test_pid_parameters_declared():
    """All 9 PID gain parameters must be declared in the controller."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    missing = [p for p in REQUIRED_PID_PARAMS if p not in source]
    assert not missing, (
        f"Missing PID parameter declarations: {', '.join(missing)}. "
        f"All 9 gains (kp/kd/ki for x/y/z) must be declared as ROS parameters."
    )


def test_velocity_limits_declared():
    """Velocity saturation parameters must be declared."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    missing = [p for p in VELOCITY_PARAMS if p not in source]
    assert not missing, (
        f"Missing velocity limit parameters: {', '.join(missing)}. "
        f"You must cap the commanded velocities for safety."
    )


# ── PID implementation checks (hard fail) ───────────────────


def test_has_error_calculation():
    """PID controller must compute error = goal - measured."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    # Look for subtraction patterns that indicate error computation
    has_error = (
        "error" in source.lower()
        or "e_x" in source or "e_y" in source or "e_z" in source
        or "err" in source.lower()
    )
    assert has_error, (
        "No error calculation found. "
        "Your PID controller must compute error = goal_position - current_position."
    )


def test_has_integral_term():
    """PID must accumulate integral of error."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    source_lower = source.lower()
    has_integral = (
        "integral" in source_lower
        or "i_sum" in source_lower
        or "sum_error" in source_lower
        or "error_sum" in source_lower
        or "+=" in source  # accumulation pattern
    )
    assert has_integral, (
        "No integral accumulation found. "
        "Your PID controller must track the integral (sum) of error over time."
    )


def test_has_derivative_term():
    """PID must compute derivative of error."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    source_lower = source.lower()
    has_derivative = (
        "prev_error" in source_lower
        or "previous_error" in source_lower
        or "last_error" in source_lower
        or "e_prev" in source_lower
        or "error_prev" in source_lower
        or ("/ dt" in source_lower or "/dt" in source_lower or "/ self.dt" in source_lower)
    )
    assert has_derivative, (
        "No derivative computation found. "
        "Your PID controller must compute the rate of change of error "
        "(using previous error and time step dt)."
    )


def test_has_dt_computation():
    """Controller must compute time step for discrete PID."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    has_dt = (
        "dt" in source
        or "delta_t" in source
        or "time_step" in source
        or "get_clock" in source
        or "Time" in source
    )
    assert has_dt, (
        "No time step (dt) computation found. "
        "Discrete PID requires computing dt between control loop iterations."
    )


# ── ROS integration checks (hard fail) ──────────────────────


def test_subscribes_to_goal_pose():
    """Must subscribe to /goal_pose for target waypoints."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    assert "goal_pose" in source, (
        "No subscription to 'goal_pose' topic found. "
        "The controller must receive target positions from /goal_pose."
    )


def test_publishes_cmd_vel():
    """Must publish to /crazyflie/cmd_vel."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    assert "cmd_vel" in source, (
        "No publisher for 'cmd_vel' topic found. "
        "The controller must publish velocity commands to /crazyflie/cmd_vel."
    )


def test_uses_tf_transforms():
    """Must use TF to get current drone position."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    has_tf = (
        "TransformListener" in source
        or "tf2_ros" in source
        or "lookup_transform" in source
        or "Buffer" in source
    )
    assert has_tf, (
        "No TF transform usage found. "
        "The controller must read the drone's position via TF "
        "(map -> crazyflie/base_footprint)."
    )


def test_imports_twist():
    """Must import Twist for velocity commands."""
    source, tree = _get_controller_source()
    assert source is not None, "Could not read controller source"
    assert "Twist" in source, (
        "Twist message type not imported. "
        "You need geometry_msgs.msg.Twist for publishing velocity commands."
    )


# ── PID value reasonableness (warnings) ─────────────────────


def test_pid_values_reasonable():
    """Check that declared PID defaults are in a reasonable range."""
    source, tree = _get_controller_source()
    if source is None:
        return

    # Extract float literals that appear near parameter names
    # Look for patterns like: kp_x, 0.6 or kp_x=0.6
    numbers = re.findall(
        r'(?:kp_|kd_|ki_|max_v_)[xyz]\S*?\s*[\,\=]\s*(-?[\d]+\.[\d]+)',
        source
    )
    floats = [float(n) for n in numbers]

    if not floats:
        warnings.warn("Could not extract PID default values for reasonableness check")
        return

    print(f"Extracted parameter values: {floats}")

    # Check for obviously wrong values
    for v in floats:
        if v > 50.0:
            warnings.warn(
                f"PID parameter value {v} seems very high. "
                f"Typical Kp values for Crazyflie are 0.5-4.0."
            )
        if v < 0:
            warnings.warn(
                f"Negative PID parameter value {v} found. "
                f"PID gains should generally be non-negative."
            )


def test_z_gains_differ_from_xy():
    """Z-axis gains should differ from X/Y due to gravity compensation."""
    source, tree = _get_controller_source()
    if source is None:
        return

    # Try to extract kp_x and kp_z defaults
    kp_x_match = re.search(r'kp_x\S*?\s*[\,\=]\s*([\d]+\.[\d]+)', source)
    kp_z_match = re.search(r'kp_z\S*?\s*[\,\=]\s*([\d]+\.[\d]+)', source)

    if kp_x_match and kp_z_match:
        kp_x = float(kp_x_match.group(1))
        kp_z = float(kp_z_match.group(1))
        if kp_x == kp_z:
            warnings.warn(
                f"kp_x ({kp_x}) and kp_z ({kp_z}) have identical values. "
                f"The Z-axis typically needs higher gains for gravity compensation."
            )


# ── Entry points (warnings) ─────────────────────────────────


def test_setup_entry_points():
    pkg = _find_ros2_package()
    if pkg is None:
        return
    setup_path = os.path.join(pkg, "setup.py")
    if not os.path.isfile(setup_path):
        return
    with open(setup_path, "r", errors="replace") as f:
        content = f.read()
    missing = {ep for ep in EXPECTED_ENTRY_POINTS if ep not in content}
    if missing:
        warnings.warn(
            f"Entry points not found in setup.py: {', '.join(sorted(missing))}. "
            f"Expected: goal_3d_controller, trajectory_publisher, plotting"
        )


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
