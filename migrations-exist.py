#!/usr/bin/env python3

import os
import re
import sys
import subprocess


MANAGE = None
for root, dirs, files in os.walk(""):
    if root[0] == ".":
        raise Exception((root, dirs, files))
    if "manage.py" in files:
        MANAGE = os.path.join(root, "manage.py")
        break

if MANAGE is None:
    "manage.py not found in this repository"
    sys.exit(1)


if sys.argv[1:]:
    # Run migrations to see if anything is produced
    makemigrations = subprocess.run(
        [MANAGE, "makemigrations"], capture_output=True
    )
    stdout = makemigrations.stdout.decode("utf-8")
    if stdout.startswith("Migrations for"):
        print("Unmigrated model changes detected")
        sys.exit(1)
    # Check for unstaged migrations
    status = (
        subprocess.run(["git", "status", "-s"], capture_output=True)
        .stdout.decode("utf-8")
        .split("\n")
    )
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
    # Nothing seems to have gone wrong, but make sure there's not unexpected output
    if not stdout.startswith("No changes detected"):
        raise Exception((stdout, makemigrations.stderr.decode("utf-8")))
