import os
import subprocess
import sys
import pathlib

def main():
    # To debug the tool, you can uncomment the following line to enable debug mode:
    # os.environ['FLUTTER_TOOL_ARGS'] = "--enable-asserts " + os.environ.get('FLUTTER_TOOL_ARGS', '')

    # script_dir = os.path.dirname(os.path.abspath(__file__))
    flutter_root_env = os.environ.get('FLUTTER_ROOT')
    if flutter_root_env:
        flutter_root = os.path.abspath(flutter_root_env)
    else:
        flutter_root = os.path.abspath(os.path.join(pathlib.Path.home(), "Downloads", "flutter"))

    # If available, add location of bundled mingit to PATH
    mingit_path = os.path.join(flutter_root, "bin", "mingit", "cmd")
    if os.path.exists(mingit_path):
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + mingit_path

    # We test if Git is available on the Host as we run git in shared.bat
    # Test if the flutter directory is a git clone, otherwise git rev-parse HEAD would fail
    if not os.path.exists(os.path.join(flutter_root, ".git")):
        print("Error: The Flutter directory is not a clone of the GitHub project.")
        print("       The flutter tool requires Git in order to operate properly;")
        print("       to set up Flutter, run the following command:")
        print("       git clone -b stable https://github.com/flutter/flutter.git")
        sys.exit(1)

    # Include shared scripts
    shared_bin = os.path.join(flutter_root, "bin", "internal", "shared.py")
    subprocess.check_call(["python", shared_bin])

    flutter_tools_dir = os.path.join(flutter_root, "packages", "flutter_tools")
    cache_dir = os.path.join(flutter_root, "bin", "cache")
    script_path = os.path.join(flutter_tools_dir, "bin", "flutter_tools.dart")
    dart_sdk_path = os.path.join(cache_dir, "dart-sdk")
    dart = os.path.join(dart_sdk_path, "bin", "dart.exe")

    command = [dart, "run", "--resident", "--packages=" + os.path.join(flutter_tools_dir, ".dart_tool", "package_config.json")]
    if 'FLUTTER_TOOL_ARGS' in os.environ:
        command.extend(os.environ['FLUTTER_TOOL_ARGS'].split())
    command.extend([script_path] + sys.argv[1:])
    subprocess.run(command, check=True)