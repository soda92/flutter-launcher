import os
import pathlib
import sys

def get_flutter_root_path():
    """Determines the FLUTTER_ROOT path.
    Defaults to user's Downloads folder/flutter if FLUTTER_ROOT env var is not set.
    """
    flutter_root_env = os.environ.get('FLUTTER_ROOT')
    if flutter_root_env:
        return os.path.abspath(flutter_root_env)
    else:
        return os.path.abspath(os.path.join(pathlib.Path.home(), "Downloads", "flutter"))

def get_dart_exe_path(flutter_root):
    """Gets the path to the Dart executable within the Flutter SDK cache."""
    cache_dir = os.path.join(flutter_root, "bin", "cache")
    dart_sdk_path = os.path.join(cache_dir, "dart-sdk")
    return os.path.join(dart_sdk_path, "bin", "dart.exe") # Assumes .exe for Windows

def ensure_git_repository(flutter_root):
    """Checks if flutter_root is a git repository and exits if not."""
    if not os.path.exists(os.path.join(flutter_root, ".git")):
        print("Error: The Flutter directory is not a clone of the GitHub project.", file=sys.stderr)
        print("       The flutter tool requires Git in order to operate properly;", file=sys.stderr)
        print("       to set up Flutter, run the following command:", file=sys.stderr)
        print("       git clone -b stable https://github.com/flutter/flutter.git", file=sys.stderr)
        sys.exit(1)

def add_mingit_to_path(flutter_root):
    """Adds bundled mingit to PATH if it exists."""
    mingit_path = os.path.join(flutter_root, "bin", "mingit", "cmd")
    if os.path.exists(mingit_path):
        if "PATH" in os.environ:
            os.environ["PATH"] = os.environ["PATH"] + os.pathsep + mingit_path
        else:
            os.environ["PATH"] = mingit_path