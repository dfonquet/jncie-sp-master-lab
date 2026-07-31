# JPR-962 Blueprint Coverage

Source: [official JNCIE-SP certification and exam objectives](https://www.juniper.net/us/en/training/certification/tracks/service-provider-routing-switching/jncie-sp.html).

The physical topology provides the reusable infrastructure. Logical systems,
routing instances, logical tunnels, and optional collectors extend scenarios
without permanently consuming additional vMX resources.

| Domain | Blueprint technologies | Optimized lab use |
| --- | --- | --- |
| System management and monitoring | Stateless control-plane protection; OP, event and commit scripts; secured streaming telemetry; SNMPv3; IPv4/IPv6 sampling; local and remote syslog | Apply to P/PE/RR nodes; use AUTO1 and optional on-demand collectors |
| Core technologies | IS-IS, policy, BFD, BGP and authentication, RIB groups, RSVP and protection, LDP, administrative groups, SR-MPLS, LDP/SR interworking, CoS | Four-node redundant P core, four dual-homed PEs, and two future RRs |
| Edge services | Interprovider VPNs, PE-CE protocols, hub-and-spoke L3VPN, VPN Internet access, VPN filtering, BGP/LDP VPLS, VLAN-aware and VLAN-based EVPN, BUM policing, MAC learning security | Four physical PEs plus logical-system customer and ASBR overlays |

## Beyond the blueprint

The exercise catalog may additionally cover RPKI origin validation, BMP,
gNMI/OpenConfig, infrastructure-as-code validation, configuration rollback,
failure injection, route-leak prevention, and operational acceptance tests.
These are not enabled in the generated baseline.
