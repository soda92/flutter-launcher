import os
import subprocess
import sys
from .common import get_flutter_root_path, get_dart_exe_path, add_mingit_to_path, ensure_git_repository
from .shared import main as run_shared_main

def main():
    try:
        # To debug the tool, you can uncomment the following line to enable debug mode:
        # os.environ['FLUTTER_TOOL_ARGS'] = "--enable-asserts " + os.environ.get('FLUTTER_TOOL_ARGS', '')

        flutter_root = get_flutter_root_path()

        # If available, add location of bundled mingit to PATH
        add_mingit_to_path(flutter_root)

        # Ensure the Flutter directory is a git clone
        ensure_git_repository(flutter_root)

        # Run shared setup. This will also handle SDK downloads/updates if necessary.
        run_shared_main(flutter_root_override=flutter_root)

        dart_exe = get_dart_exe_path(flutter_root)
        flutter_tools_dir = os.path.join(flutter_root, "packages", "flutter_tools")
        flutter_tools_script_path = os.path.join(flutter_tools_dir, "bin", "flutter_tools.dart")

        command = [
            dart_exe, "run", "--resident",
            "--packages=" + os.path.join(flutter_tools_dir, ".dart_tool", "package_config.json")
        ]
        if 'FLUTTER_TOOL_ARGS' in os.environ:
            command.extend(os.environ['FLUTTER_TOOL_ARGS'].split())
        command.extend([flutter_tools_script_path] + sys.argv[1:])
        subprocess.run(command, check=True)

    except KeyboardInterrupt:
        print("\nFlutter Dev command cancelled by user.", file=sys.stderr)
        sys.exit(130) # Standard exit code for ^C
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)