import os
import subprocess
import sys
import pathlib
import shutil
import time
import glob

def main(flutter_root_override=None):
    if flutter_root_override:
        flutter_root = os.path.abspath(flutter_root_override)
    else:
        # This path is taken if flutter_root_override is not provided
        flutter_root_env = os.environ.get('FLUTTER_ROOT')
        if flutter_root_env:
            flutter_root = os.path.abspath(flutter_root_env)
        else:
            flutter_root = os.path.abspath(os.path.join(pathlib.Path.home(), "Downloads", "flutter"))

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
        print("Building flutter tool...", file=sys.stderr, flush=True)

        # 1. Cleanup Old Version Files
        version_file = os.path.join(flutter_root, "version")
        version_json_file = os.path.join(cache_dir, "flutter.version.json")
        dartignore_file = os.path.join(cache_dir, ".dartignore")

        try:
            if os.path.exists(version_file):
                os.remove(version_file)
            if os.path.exists(version_json_file):
                os.remove(version_json_file)
            with open(dartignore_file, 'w') as f:
                pass # Create empty .dartignore
        except OSError as e:
            print(f"Error cleaning up old version files: {e}", file=sys.stderr)
            # Decide if this is fatal or not, original script doesn't explicitly exit here.

        # 2. Run `pub upgrade`
        # Prepare environment for pub upgrade
        pub_env = os.environ.copy()
        pub_env_parts = []
        if os.environ.get('CI') == 'true' or \
           os.environ.get('BOT') == 'true' or \
           os.environ.get('CONTINUOUS_INTEGRATION') == 'true' or \
           os.environ.get('CHROME_HEADLESS') == '1':
            pub_env_parts.append('flutter_bot')
        else:
            pub_env_parts.append('flutter_install')
        
        existing_pub_env = pub_env.get('PUB_ENVIRONMENT', '')
        if existing_pub_env:
            pub_env_parts.insert(0, existing_pub_env)
        pub_env['PUB_ENVIRONMENT'] = ':'.join(pub_env_parts)
        pub_env['PUB_SUMMARY_ONLY'] = '1'

        # Note: The batch script has a conditional PUB_CACHE logic based on pub_cache_path.
        # This is omitted here as pub_cache_path is not defined in the provided context.
        # If FLUTTER_ROOT/.pub-cache is the convention, it could be added:
        # if not pub_env.get('PUB_CACHE'):
        #     potential_pub_cache = os.path.join(flutter_root, ".pub-cache")
        #     if os.path.isdir(potential_pub_cache):
        #         pub_env['PUB_CACHE'] = potential_pub_cache

        total_tries = 10
        for i in range(total_tries):
            print("Running pub upgrade...", file=sys.stderr, flush=True)
            try:
                # PUSHD flutter_tools_dir is handled by cwd
                subprocess.run(
                    [dart, "pub", "upgrade", "--suppress-analytics"],
                    cwd=flutter_tools_dir,
                    env=pub_env,
                    check=True,
                    stdout=sys.stderr, # Show pub upgrade output on stderr
                    stderr=subprocess.STDOUT
                )
                break # Success
            except subprocess.CalledProcessError as e:
                print(f"Error ({e.returncode}): Unable to 'pub upgrade' flutter tool. Retrying in five seconds... ({total_tries - 1 - i} tries left)", file=sys.stderr, flush=True)
                if i < total_tries - 1:
                    time.sleep(5)
                else:
                    print(f"Error: 'pub upgrade' still failing after {total_tries} tries.", file=sys.stderr, flush=True)
                    sys.exit(e.returncode or 1)
        
        # 3. Manage Old Snapshot File
        snapshot_path_old_base = snapshot_path + ".old"
        suffix = 1
        target_old_path = snapshot_path_old_base
        # Check if snapshot_path_old_base itself is available (without suffix)
        if os.path.exists(target_old_path):
            target_old_path = f"{snapshot_path_old_base}{suffix}"
            while os.path.exists(target_old_path):
                suffix += 1
                target_old_path = f"{snapshot_path_old_base}{suffix}"
        
        if os.path.exists(snapshot_path):
            try:
                shutil.move(snapshot_path, target_old_path)
            except OSError as e:
                print(f"Warning: Could not move old snapshot: {e}", file=sys.stderr)

        # 4. Create New Snapshot
        snapshot_command = [dart]
        flutter_tool_args = os.environ.get('FLUTTER_TOOL_ARGS', '')
        if flutter_tool_args:
            snapshot_command.extend(flutter_tool_args.split())
        snapshot_command.extend([
            "--verbosity=error",
            f"--snapshot={snapshot_path}",
            "--snapshot-kind=app-jit",
            f"--packages={os.path.join(flutter_tools_dir, '.dart_tool', 'package_config.json')}"
        ])
        if not flutter_tool_args: # Add --no-enable-mirrors only if FLUTTER_TOOL_ARGS was empty
            snapshot_command.append("--no-enable-mirrors")
        snapshot_command.append(script_path)

        try:
            subprocess.run(snapshot_command, check=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error: Unable to create dart snapshot for flutter tool. Exit code: {e.returncode}", file=sys.stderr, flush=True)
            sys.exit(e.returncode or 1)

        # 5. Update Stamp File
        try:
            with open(stamp_path, 'w') as f:
                f.write(compilekey)
        except IOError as e:
            print(f"Error: Unable to write to stamp file {stamp_path}: {e}", file=sys.stderr, flush=True)
            sys.exit(1)

        # 6. Cleanup Numbered Old Snapshots
        try:
            for old_snapshot_file in glob.glob(snapshot_path + ".old*"):
                os.remove(old_snapshot_file)
        except OSError as e:
            print(f"Warning: Could not delete old snapshot files: {e}", file=sys.stderr)

        print("Flutter tool built.", file=sys.stderr, flush=True)