#!/usr/bin/env python3

import os
import re
import sys
import subprocess

import django
import django.apps


def locate(name, start=".", skip_hidden=True):
    """
    Search for a file by name in subdirectories
    """
    for root, dirs, files in os.walk(start):
        base_dir = os.path.basename(root)
        if root == start or not (skip_hidden and base_dir.startswith(".")):
            if name in files:
                return os.path.join(root, name)


def setup_django_environment(manage_py):
    """
    Create the same environment that 'manage.py shell' would have
    """
    BASE_DIR = os.path.dirname(os.path.normpath(manage_py))
    if BASE_DIR:
        sys.path.insert(0, BASE_DIR)

    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = lines_from_command(
            manage_py,
            "shell",
            "-c",
            "import os;print(os.environ['DJANGO_SETTINGS_MODULE'])",
            only=1,
        )

    django.setup()


def lines_from_command(*args, only=None):
    """
    Runs a subprocess, and returns its output as a list of lines
    """
    process = subprocess.run(list(args), capture_output=True)
    if process.stderr:
        fail(process.stderr.decode("utf-8"))
    lines = process.stdout.decode("utf-8").split("\n")
    if only == 1:
        return lines[0]
    return lines if lines and lines[-1] else lines[:-1]


def fail(message=None):
    if message:
        print(message)
    sys.exit(1)


def main(changed_paths):
    GIT_ROOT = lines_from_command("git", "rev-parse", "--show-toplevel")[0]

    MANAGE = locate("manage.py", start=GIT_ROOT)

    if MANAGE is None:
        fail("manage.py not found in this repository")

    setup_django_environment(MANAGE)

    app_abs_paths = [app.path + "/" for app in django.apps.apps.get_app_configs()]
    repo_apps = [path for path in app_abs_paths if path.startswith(GIT_ROOT + "/")]

    if not repo_apps:
        fail("No code from this repository is included in settings.INSTALLED_APPS")

    # Make sure that its package is in settings.INSTALLED_APPS
    for model_path in changed_paths:
        model_abs_path = os.path.abspath(model_path)
        if all(not model_abs_path.startswith(app_path) for app_path in repo_apps):
            fail(
                "{!r} is not part of an app in settings.INSTALLED_APPS".format(
                    model_abs_path
                )
            )

    # Run migrations to see if anything is produced
    makemigrations = subprocess.run(
        [MANAGE, "makemigrations", "--dry-run"], capture_output=True
    )
    stdout = makemigrations.stdout.decode("utf-8")
    if stdout.startswith("Migrations for"):
        fail()

    # Check for unstaged migrations
    status = lines_from_command("git", "status", "-s")
    migrations_pattern = r".*/migrations/.*\.py"
    pattern = r"(?P<staged>[AM?])(?P<unstaged>[AM?]) (?P<path>{})".format(
        migrations_pattern
    )
    matches = [re.fullmatch(pattern, line) for line in status]
    found = False
    for match in matches:
        if match and match.groupdict()["unstaged"] != " ":
            if not found:
                found = True
                print("Unstaged migrations exist:\n")
            print(match.groupdict()["path"])
    if found:
        sys.exit(1)


if __name__ == "__main__":
    if sys.argv[1:]:
        main(sys.argv[1:])
