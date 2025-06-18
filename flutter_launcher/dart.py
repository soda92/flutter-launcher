import os
import subprocess
import sys
import pathlib

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flutter_root_env = os.environ.get('FLUTTER_ROOT')
    if flutter_root_env:
        flutter_root = os.path.abspath(flutter_root_env)
    else:
        flutter_root = os.path.abspath(os.path.join(pathlib.Path.home(), "Downloads", "flutter"))

    # Include shared scripts
    shared_bin = os.path.join(flutter_root, "bin", "internal", "shared.py")
    subprocess.check_call(["python", shared_bin])

    cache_dir = os.path.join(flutter_root, "bin", "cache")
    dart_sdk_path = os.path.join(cache_dir, "dart-sdk")
    dart = os.path.join(dart_sdk_path, "bin", "dart.exe")

    command = [dart] + sys.argv[1:]
    subprocess.run(command, check=True)