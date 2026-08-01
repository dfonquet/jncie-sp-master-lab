# JNCIE-SP Master Topology

The master profile contains fourteen Juniper vMX routers, AUTO1 on the
management network, and twenty-five
point-to-point links. It intentionally provides only dual-stack addressing and
a single IS-IS Level 2 underlay. All advanced service-provider technologies
remain student work.

```mermaid
flowchart TB
  RR1([RR1]) --- P1((P1))
  RR1 --- P4((P4))
  RR2([RR2]) --- P3((P3))
  RR2 --- P6((P6))

  P1 --- P2((P2))
  P2 --- P3
  P3 --- P4
  P4 --- P5((P5))
  P5 --- P6
  P6 --- P1
  P1 -. metric 20 .- P4
  P2 -. metric 20 .- P5
  P3 -. metric 20 .- P6

  PE1[PE1] --- P1
  PE1 --- P2
  PE2[PE2] --- P2
  PE2 --- P3
  PE3[PE3] --- P3
  PE3 --- P4
  PE4[PE4] --- P4
  PE4 --- P5
  PE5[PE5] --- P5
  PE5 --- P6
  PE6[PE6] --- P6
  PE6 --- P1
```

## Design rationale

- The six-P ring survives any single core-link failure.
- Three higher-metric chords provide alternate paths and useful metric and
  convergence exercises without forcing an artificial full mesh.
- Every PE is dual-homed to adjacent P routers.
- Each RR candidate has two physically diverse underlay paths.
- RR nodes participate only in the IS-IS base. No BGP role is preconfigured.
- `/31` and `/127` point-to-point addressing follows operationally efficient
  provider practice.
- Startup delays are spaced by 45 seconds to control vMX boot pressure.

## Student boundary

The generated base does not configure BGP, MPLS, LDP, RSVP, segment routing,
VPNs, multicast, class of service, security policies, telemetry, or service
automation. Those capabilities are intentionally left for study exercises.
