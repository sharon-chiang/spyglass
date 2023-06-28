#!/usr/bin/env python
import os
import sys
import tempfile

shared_modules = [r"common\_%", r"spikesorting\_%", r"decoding\_%"]


def add_user(user_name):
    """Add existing user to the database. Requires /home/{user_name} dir."""
    if os.path.isdir(f"/home/{user_name}"):
        print("Creating database user ", user_name)
    else:
        sys.exit(f"Error: user_name {user_name} does not exist in /home.")

    # create a tempoary file for the command
    file = tempfile.NamedTemporaryFile(mode="w")

    file.write(
        f"GRANT ALL PRIVILEGES ON `{user_name}"
        + r"\_%`.* TO "
        + f"`{user_name}`@'%' IDENTIFIED BY 'temppass';\n"
    )
    for module in shared_modules:
        file.write(
            f"GRANT ALL PRIVILEGES ON `{module}`.* TO `{user_name}`@'%';\n"
        )
    file.write(f"GRANT SELECT ON `%`.* TO `{user_name}`@'%';\n")
    file.flush()

    # run those commands in sql
    os.system(f"mysql -p -h lmf-db.cin.ucsf.edu < {file.name}")


if __name__ == "__main__":
    add_user(sys.argv[1])
