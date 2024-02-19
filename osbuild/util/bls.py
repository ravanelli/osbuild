import glob
import os
import re

"""
Function for appending parameters to
Boot Loader Specification (BLS).
"""

def options_append(root_path, kernel_arguments):
    """
    Add kernel arguments to the Boot Loader Specification (BLS) configuration files.
    There is unlikely to be more than one BLS config, but just in case, we'll iterate over them.

    Parameters
    ----------

    root_path (str): The root path for locating BLS configuration files.
    kernel_arguments (list): A list of kernel arguments to be added.

    """
    # There is unlikely to be more than one bls config, but just
    # in case we'll iterate over them.
    entries = []
    for entry in glob.glob(f"{root_path}/loader/entries/*.conf"):
        entries.append(entry)
        # Read in the file and then append to the options line.
        with open(entry, encoding="utf8") as f:
            lines = f.read().splitlines()
        with open(entry, "w", encoding="utf8") as f:
            for line in lines:
                if line.startswith('options '):
                    f.write(f"{line} {' '.join(kernel_arguments)}\n")
                else:
                    f.write(f"{line}\n")
    assert len(entries) != 0
    print(f"Added {','.join(kernel_arguments)} to: {','.join(entries)}")
    return 0
