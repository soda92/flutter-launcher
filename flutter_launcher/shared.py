import os
import subprocess
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flutter_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    flutter_tools_dir = os.path.join(flutter_root, "packages", "flutter_tools")
    cache_dir = os.path.join(flutter_root, "bin", "cache")
    snapshot_path = os.path.join(cache_dir, "flutter_tools.snapshot")
    stamp_path = os.path.join(cache_dir, "flutter_tools.stamp")
    script_path = os.path.join(flutter_tools_dir, "bin", "flutter_tools.dart")
    dart_sdk_path = os.path.join(cache_dir, "dart-sdk")
    engine_stamp = os.path.join(cache_dir, "engine-dart-sdk.stamp")
    engine_version_path = os.path.join(cache_dir, "engine.stamp")
    dart = os.path.join(dart_sdk_path, "bin", "dart.exe")

    # Ensure that bin/cache exists.
    os.makedirs(cache_dir, exist_ok=True)

    # If the cache still doesn't exist, fail with an error that we probably don't have permissions.
    if not os.path.exists(cache_dir):
        print("Error: Unable to create cache directory at", file=sys.stderr)
        print(f"            {cache_dir}", file=sys.stderr)
        print("", file=sys.stderr)
        print("        This may be because flutter doesn't have write permissions for", file=sys.stderr)
        print("        this path. Try moving the flutter directory to a writable location,", file=sys.stderr)
        print("        such as within your home directory.", file=sys.stderr)
        sys.exit(1)

    # Check that git exists and get the revision.
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Error: Unable to find git in your PATH.", file=sys.stderr)
        sys.exit(1)

    try:
        revision = subprocess.check_output(["git", "-C", flutter_root, "rev-parse", "HEAD"]).decode().strip()
    except subprocess.CalledProcessError:
        print("Error: The Flutter directory is not a clone of the GitHub project.", file=sys.stderr)
        print("       The flutter tool requires Git in order to operate properly;", file=sys.stderr)
        print("       to set up Flutter, run the following command:", file=sys.stderr)
        print("       git clone -b stable https://github.com/flutter/flutter.git", file=sys.stderr)
        sys.exit(1)

    compilekey = f"{revision}:{os.environ.get('FLUTTER_TOOL_ARGS', '')}"

    # Invalidate cache if:
    #  * SNAPSHOT_PATH is not a file, or
    #  * STAMP_PATH is not a file, or
    #  * STAMP_PATH is an empty file, or
    #  * Contents of STAMP_PATH is not what we are going to compile, or
    #  * pubspec.yaml last modified after pubspec.lock

    def should_snapshot():
        if not os.path.exists(engine_stamp):
            return True
        with open(engine_version_path, "r") as f:
            dart_required_version = f.read().strip()
        with open(engine_stamp, "r") as f:
            dart_installed_version = f.read().strip()
        if dart_required_version != dart_installed_version:
            return True
        if not os.path.exists(snapshot_path) or not os.path.exists(stamp_path):
            return True
        with open(stamp_path, "r") as f:
            stamp_value = f.read().strip()
        if stamp_value != compilekey:
            return True
        pubspec_yaml_path = os.path.join(flutter_tools_dir, "pubspec.yaml")
        pubspec_lock_path = os.path.join(flutter_tools_dir, "pubspec.lock")
        if os.path.getmtime(pubspec_yaml_path) > os.path.getmtime(pubspec_lock_path):
            return True
        return False

    if should_snapshot():
        print("Building flutter tool...", file=sys.stderr)
        # Invalidate cache and build snapshot here (implementation details...)