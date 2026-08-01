# JNCIE-SP JPR-962 Blueprint Coverage

Last verified: **2026-08-01** against the [official Juniper JNCIE-SP page](https://www.juniper.net/us/en/training/certification/tracks/service-provider-routing-switching/jncie-sp.html).
JPR-962 is an English, six-hour hands-on lab. This matrix paraphrases the
public objectives; it does not represent Juniper's confidential exam topology.

Status vocabulary: Planned, Implemented, Statically validated, Runtime
validated, Blocked by image, and Out of scope. “Runtime validated” is used only
when evidence exists; no advanced scenario currently carries that status.

## System Management and Monitoring

| Domain | Objective | Physical profile | Logical roles | Scenario ID | Implementation status | Runtime validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| System management | Stateless control-plane protection | daily | traffic endpoint | SYS-CP-001 | Planned | Not run | Scenario catalog |
| System management | OP scripts | daily | AUTO1 | SYS-OP-001 | Planned | Not run | Scenario catalog |
| System management | Event scripts | daily | syslog collector | SYS-EVENT-001 | Planned | Not run | Scenario catalog |
| System management | Commit scripts | daily | AUTO1 | SYS-COMMIT-001 | Planned | Not run | Scenario catalog |
| System management | Secured streaming telemetry | optimized | telemetry collector | SYS-TELEM-001 | Planned | Not run | Logical overlay |
| System management | SNMPv3 authentication and privacy | daily | SNMPv3 manager | SYS-SNMP-001 | Planned | Not run | Logical overlay |
| System management | IPv4 traffic sampling | optimized | collector | SYS-SAMPLE4-001 | Planned | Not run | Logical overlay |
| System management | IPv6 traffic sampling | optimized | collector | SYS-SAMPLE6-001 | Planned | Not run | Logical overlay |
| System management | Local and remote logging | daily | syslog collector | SYS-LOG-001 | Planned | Not run | Logical overlay |

## Core Technologies

| Domain | Objective | Physical profile | Logical roles | Scenario ID | Implementation status | Runtime validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core | IS-IS configuration, modification and troubleshooting | daily | provider core | CORE-ISIS-001 | Implemented | Not run | Scenario task and generated baseline |
| Core | Routing policy | daily | customer and Internet roles | CORE-POLICY-001 | Implemented | Not run | Scenario task |
| Core | BFD failure detection | optimized | provider core | CORE-BFD-001 | Implemented | Not run | Scenario task |
| Core | BGP configuration and troubleshooting | daily | RR and PE | CORE-BGP-001 | Planned | Not run | Scenario catalog |
| Core | BGP session security | daily | Internet gateway | CORE-BGP-AUTH-001 | Implemented | Not run | Scenario task |
| Core | RIB groups | daily | customer and Internet roles | CORE-RIB-GROUP-001 | Implemented | Not run | Scenario task |
| Core | RSVP-signaled LSPs | optimized | P/PE | CORE-RSVP-001 | Planned | Not run | Physical topology |
| Core | RSVP LSP protection | optimized | P/PE | CORE-RSVP-PROT-001 | Planned | Not run | Physical topology |
| Core | LDP LSPs and mixed-core behavior | optimized | P/PE | CORE-LDP-001 | Planned | Not run | Physical topology |
| Core | Administrative groups | optimized | P/PE | CORE-ADMIN-GROUP-001 | Planned | Not run | Higher-diversity paths |
| Core | SR-MPLS | optimized | P/PE | CORE-SR-001 | Planned | Not run | Physical topology |
| Core | LDP and SR-MPLS interconnection | master | logical domains | CORE-LDP-SR-001 | Planned | Not run | Logical overlay |
| Core | Classification, prioritization and consistent CoS | optimized | traffic endpoints | CORE-COS-001 | Planned | Not run | Logical overlay |

## Edge Services

| Domain | Objective | Physical profile | Logical roles | Scenario ID | Implementation status | Runtime validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Edge | Interprovider VPNs | master | ASBR and second SP | EDGE-INTERPROVIDER-001 | Planned | Not run | Logical overlay |
| Edge | Multiple PE-to-CE protocols | daily | Customer A | EDGE-PECE-001 | Planned | Not run | Logical overlay |
| Edge | Hub-and-spoke L3VPN | daily | Customer A hub/spokes | EDGE-L3VPN-HS-001 | Planned | Not run | Logical overlay |
| Edge | Internet access for L3VPN | optimized | Internet gateway | EDGE-INET-001 | Planned | Not run | Logical overlay |
| Edge | VPN route filtering | daily | PEs | EDGE-VPN-FILTER-001 | Planned | Not run | Scenario catalog |
| Edge | BGP-signaled VPLS | optimized | Customer B | EDGE-BGP-VPLS-001 | Planned | Not run | Logical overlay |
| Edge | LDP-signaled VPLS | optimized | Customer B | EDGE-LDP-VPLS-001 | Planned | Not run | Logical overlay |
| Edge | VLAN-aware EVPN | optimized | Customer C | EDGE-EVPN-AWARE-001 | Planned | Not run | Logical overlay |
| Edge | VLAN-based EVPN | optimized | Customer C | EDGE-EVPN-VLAN-001 | Planned | Not run | Logical overlay |
| Edge | BUM policing | optimized | Customer B/C | EDGE-BUM-001 | Planned | Not run | Logical overlay |
| Edge | MAC learning security | optimized | Customer B/C | EDGE-MACSEC-001 | Planned | Not run | Logical overlay |

## Supplementary multicast coverage

Juniper's exam description mentions multicast, but the current high-level
objective table does not publish multicast as a separate domain. These are
supplementary study scenarios rather than a claimed fourth official domain.

| Topic | Profile | Logical roles | Scenario ID | Status |
| --- | --- | --- | --- | --- |
| PIM sparse mode and RP reachability | optimized | source, receiver, RP | MC-PIM-001 | Planned |
| Static RP and BSR where supported | optimized | source, receiver, RP | MC-RP-001 | Planned |
| IGMP and IPv4 multicast forwarding | daily | source and receiver | MC-IGMP-001 | Planned |
| RPF, `(*,G)` and `(S,G)` troubleshooting | optimized | source and receiver | MC-RPF-001 | Planned |
| Multicast VPN extensions | master | customer overlays | MC-MVPN-001 | Planned |
