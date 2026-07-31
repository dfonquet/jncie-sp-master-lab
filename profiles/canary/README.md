# vMX Canary Profiles

The single-node profile validates the prepared vMX image, management access,
Junos, and the forwarding plane. The dual-node profile validates real IPv4
and IPv6 forwarding before the master topology is generated.

## Interface mapping

For this vMX 21.3R1.9 image and vrnetlab build, Containerlab `eth1` maps to
Junos `ge-0/0/1`. Junos `ge-0/0/0` is consumed by the internal vFPC dummy
adapter and must not be used as a lab-facing port. This mapping was verified
by matching the QEMU, Linux-container, and Junos interface MAC addresses.

## Validated dual link

| Node | Management | Data-plane interface | IPv4 | IPv6 |
| --- | --- | --- | --- | --- |
| VMX1 | 10.204.254.101 | ge-0/0/1 | 10.204.0.0/31 | 2001:db8:204:1::/127 |
| VMX2 | 10.204.254.102 | ge-0/0/1 | 10.204.0.1/31 | 2001:db8:204:1::1/127 |

The acceptance test requires both FPCs online and four bidirectional ping
tests (IPv4 and IPv6 from each endpoint) with zero packet loss.
