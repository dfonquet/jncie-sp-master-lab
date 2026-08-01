# Physical and Logical Network Topology

The diagrams describe this independent study platform, not an unpublished or
official Juniper exam topology. CSV inventories are authoritative; diagrams
explain the generated physical design.

## Daily profile

```mermaid
flowchart TB
  AUTO1["AUTO1 (management only)"] -. management .- MGMT[("10.204.251.0/24")]
  RR1 --- P1((P1)); RR1 --- P3((P3)); RR2 --- P2((P2)); RR2 --- P3
  P1 --- P2; P2 --- P3; P3 --- P1
  PE1 --- P1; PE1 --- P2; PE2 --- P2; PE2 --- P3; PE3 --- P3; PE3 --- P1
```

Eight vMX routers use thirteen data-plane links. The P triangle remains
connected after one core-link failure; every PE and RR candidate is dual-homed.
This is the default because it preserves useful path diversity with the lowest
routine CPU and memory pressure.

## Optimized profile

```mermaid
flowchart TB
  AUTO1 -. management .- MGMT[("10.204.252.0/24")]
  RR1 --- P1; RR1 --- P3; RR2 --- P2; RR2 --- P4
  P1 --- P2; P2 --- P3; P3 --- P4; P4 --- P1
  P1 -. "metric 20" .- P3; P2 -. "metric 20" .- P4
  PE1 --- P1; PE1 --- P2; PE2 --- P2; PE2 --- P3
  PE3 --- P3; PE3 --- P4; PE4 --- P4; PE4 --- P1
```

Ten vMX routers and eighteen links provide alternate equal and unequal paths
for RSVP-TE, primary/secondary LSPs, protection, administrative groups, BFD,
ECMP, SR-MPLS, LDP/SR interworking and path-dependent CoS exercises.

## Master profile

```mermaid
flowchart TB
  AUTO1 -. management .- MGMT[("10.204.253.0/24")]
  RR1 --- P1; RR1 --- P4; RR2 --- P3; RR2 --- P6
  P1 --- P2; P2 --- P3; P3 --- P4; P4 --- P5; P5 --- P6; P6 --- P1
  P1 -. "metric 20" .- P4; P2 -. "metric 20" .- P5; P3 -. "metric 20" .- P6
  PE1 --- P1; PE1 --- P2; PE2 --- P2; PE2 --- P3; PE3 --- P3; PE3 --- P4
  PE4 --- P4; PE4 --- P5; PE5 --- P5; PE5 --- P6; PE6 --- P6; PE6 --- P1
```

Fourteen vMX routers and twenty-five links form a six-P ring with three
higher-metric chords. Chords provide controlled alternates without replacing
normal ring paths. The profile supports broad failure injection and six-hour
integrated mock exams, but its resource cost makes it unsuitable as the daily
default.

## Interface contract

The validated local image maps Containerlab `eth1` to Junos `ge-0/0/1`;
`ge-0/0/0` is unavailable as a normal lab-facing interface. Every CSV link has
explicit `a_port` and `b_port` fields, so row ordering cannot change wiring.
AUTO1 uses only the management network and consumes no provider data-plane link.

## Logical Service and Customer Overlay

```mermaid
flowchart LR
  AUTO1[Automation] --> COLLECT["Syslog / SNMPv3 / telemetry collectors"]
  PE1 --> CAH["Customer A hub logical system"]
  PE2 --> CAS["Customer A spoke"]
  PE3 --> CAS2["Customer A spoke"]
  PE1 --> CBL2["Customer B L2 site"]
  PE4 --> CBL22["Customer B L2 site"]
  PE2 --> CCE["Customer C EVPN site"]
  PE3 --> CCE2["Customer C EVPN site"]
  PE1 --> IGW["Internet gateway / PE-CE endpoint"]
  PE4 --> ASBR["ASBR / second-provider logical system"]
  PE2 --> MS["Multicast source"]
  PE3 --> MR["Multicast receiver"]
  LINUX["On-demand lightweight traffic endpoints"] --> PE1
```

Logical systems, routing instances, logical-tunnel interfaces, bridge domains
and VLANs emulate customers, PE-CE endpoints, Internet and interprovider roles.
Lightweight on-demand containers provide traffic and collector functions.
These overlays are scenario state, never permanent baseline configuration.
