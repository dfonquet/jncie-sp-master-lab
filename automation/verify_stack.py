"""Smoke-test the Python libraries baked into the AUTO1 image."""

import ansible
import jnpr.junos
import ncclient
import netmiko


print("automation-stack-ok")
print(f"ansible={ansible.__version__}")
print(f"netmiko={netmiko.__version__}")
print(f"ncclient={ncclient.__version__}")
