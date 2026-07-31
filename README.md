# JNCIE-SP Master Lab

Independent Containerlab-based study environment for the Juniper Networks
Service Provider Routing and Switching, Expert practical exam.

The project is built in controlled stages. The first stage validates the local
vMX image, management access, forwarding plane, interfaces, and resource use.
The final topology will provide a functional IPv4/IPv6 and IS-IS foundation
while leaving advanced JNCIE-SP technologies as student exercises.

## Current status

- `canary`: validated one-node image test and two-node IPv4/IPv6 forwarding test.
- `daily`: recommended 8-vMX topology with 3 P, 3 PE, 2 RR and 13 links.
- `optimized`: extended 10-vMX topology with 4 P, 4 PE, 2 RR and 18 links.
- `master`: optional heavy 14-vMX topology retained for occasional use.

Both baselines configure management, IPv4/IPv6 loopbacks and links, and IS-IS
Level 2 only. Start with the [daily design](docs/DAILY-TOPOLOGY.md),
its [addressing plan](docs/DAILY-ADDRESSING-PLAN.md), and the
[JPR-962 coverage matrix](docs/BLUEPRINT-COVERAGE.md).

## Generate and validate

```bash
python3 tools/build_lab.py
python3 tools/validate_artifacts.py

# Optional heavy profile
JNCIE_PROFILE=full python3 tools/build_lab.py
JNCIE_PROFILE=full python3 tools/validate_artifacts.py
```

## Daily lab lifecycle

```bash
cd /srv/netlab/labs/jncie-sp-master

# Rebuild and validate generated artifacts
python3 tools/build_lab.py
python3 tools/validate_artifacts.py

# Confirm the plan without changing runtime state
sudo containerlab apply \
  -t topology/jncie-sp-daily.clab.yml \
  --dry-run

# Start the daily profile
docker build -t jncie-sp-automation:1.0 automation/
sudo containerlab deploy -t topology/jncie-sp-daily.clab.yml

# Inspect node health and host resources
docker ps --filter name=clab-jncie-sp-daily \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
free -h
uptime

# Stop the profile and recover host resources
sudo containerlab destroy -t topology/jncie-sp-daily.clab.yml
```

Only one heavy lab profile may be active at a time.

## Licensed images

Juniper vMX disk images are not included. Obtain an appropriately licensed
image from Juniper, build the local vrnetlab image described in the project
documentation, and keep all image artifacts outside this repository.

## License

Project code and documentation are released under the [MIT License](LICENSE).
Juniper software remains subject to Juniper's applicable license terms.
