#!/usr/bin/env python3

import requests
import json
import argparse
import threading
import time
from functools import cache

# Max values
MAX_THREADS = 100

# Session
SESSION = requests.Session()
SESSION.mount("https", requests.adapters.HTTPAdapter(max_retries=5))

# Semaphores
THREADS_SEM = threading.BoundedSemaphore(MAX_THREADS)


def get_package_paths(file_path):
    with open(file_path, "r") as f:
        package_paths = [line.rstrip("\n") for line in f]
    return package_paths


def get_dependencies(package_json_path):
    dtypes = [
        "dependencies",
        "optionalDependencies",
        "devDependencies",
        "peerDependencies",
    ]
    with open(package_json_path, "r") as f:
        data = json.load(f)
    dependencies = {}
    for dtype in dtypes:
        dependencies.update(data.get(dtype, ""))
    return dependencies


@cache
def is_dependency_registered(dependency_name):
    timeout = 0
    while True:
        res = SESSION.head(f"https://registry.npmjs.org/{dependency_name}")
        if res.status_code != 429:
            break
        timeout += 5
        print(f"retrying in {timeout} seconds...")
        time.sleep(timeout)

    return res.status_code == 200


def check_dependency(user, name, version):
    with THREADS_SEM:
        if not is_dependency_registered(name):
            print(f"\n\n==== Pwnable in {user}: {name} version {version} ====\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check package.json files for unregistered dependencies."
    )
    main_args_group = parser.add_mutually_exclusive_group(required=True)
    main_args_group.add_argument(
        "-p", "--p", dest="package", action="store", help="A package.json file path."
    )
    main_args_group.add_argument(
        "-pl",
        "--pl",
        dest="package_list",
        action="store",
        help="A list file of package.json file paths.",
    )
    args = parser.parse_args()

    packages = []
    if args.package_list:
        packages.extend(get_package_paths(args.package_list))
    elif args.package:
        packages.append(args.package)

    for package in packages:
        print(f"Testing: {package}")
        dependencies = get_dependencies(package)
        for name, version in dependencies.items():
            threading.Thread(target=check_dependency, args=(package, name, version)).run()


if __name__ == "__main__":
    main()
