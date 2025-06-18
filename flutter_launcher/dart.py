import subprocess
import sys
from .common import get_flutter_root_path, get_dart_exe_path
from .shared import main as run_shared_main

def main():
    try:
        flutter_root = get_flutter_root_path()

        # Run shared setup. This will also handle SDK downloads/updates if necessary.
        run_shared_main(flutter_root_override=flutter_root)

        dart_exe = get_dart_exe_path(flutter_root)

        command = [dart_exe] + sys.argv[1:]
        subprocess.run(command, check=True)

    except KeyboardInterrupt:
        print("\nDart command cancelled by user.", file=sys.stderr)
        sys.exit(130) # Standard exit code for ^C
    except subprocess.CalledProcessError as e:
        # The subprocess itself exited with an error code
        sys.exit(e.returncode)