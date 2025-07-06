#!/usr/bin/env python3
# Script to create a new migration for missing study fields

import subprocess
import sys

# Create a new migration
result = subprocess.run([
    sys.executable, "-m", "alembic", "revision", "--autogenerate", 
    "-m", "Add missing study fields"
], capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)