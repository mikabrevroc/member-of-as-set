# Member-of-AS-SET Proposal

A proposal for bidirectional verification of AS-SET membership in Internet Routing Registries (IRR).

## Overview

This project defines the `member-of-as-set` object type for IRR databases, enabling autonomous systems to declare which AS-SETs they authorize for inclusion. This creates bidirectional verification of AS-SET expansions, improving BGP routing security.

## Problem Statement

Currently, AS-SET objects are **unidirectional**:
- An AS-SET owner can include any autonomous system without authorization
- This allows malicious operators to add tier-1/content provider ASNs (Google, Microsoft, etc.) to their AS-SET
- Potential for massive route leaks (AS-HURRICANE: 411,327 prefixes could be leaked!)

## Solution

The `member-of-as-set` object allows ASNs to declare AS-SET membership:
- AS-SET owners claim: "These ASNs are in my set"
- Each ASN declares: "I authorize being in these AS-SETs"
- During AS-SET expansion, unauthorized ASNs are automatically pruned

## Documents

| File | Description |
|------|-------------|
| `draft-carbonara-irr-member-of-as-set-00.xml` | IETF Internet-Draft (RFCXML v3) |
| `IMPLEMENTATION-GUIDE.md` | Operational implementation guide |
| `poc/` | Proof-of-concept implementation |

## Proof of Concept

Located in `poc/` directory:

- `as-set-expander.sh` - Expands AS-SETs with optional verification
- `juniper-generator.sh` - Generates Juniper AS-path/prefix-list configs
- `demo.sh` - Full demonstration with attack scenarios (includes AS-HURRICANE case)
- `simulated-irr/` - Simulated IRR objects

### Running the POC

```bash
cd poc
./demo.sh
```

Demonstrates:
1. Legitimate customer AS-SET (all authorized)
2. **AS-HURRICANE protection** (411,327 prefixes - CATASTROPHIC if leaked)
3. Content provider protection (Google: 7,259 prefixes, Amazon: 18,547 prefixes)
4. Comparison: AS-path filtering vs prefix-list filtering

## Key Features

- **Backward compatible**: ASNs without member-of-as-set objects accepted by default
- **No IRR changes needed**: Uses standard RPSL objects
- **Incremental deployment**: Large ASNs can opt-in first
- **Complements RPKI**: Adds AS-path validation, doesn't replace origin validation
- **Catastrophic leak prevention**: AS-HURRICANE (411K prefixes) protected

## Real-World Impact

From POC analysis of actual IRR data:

| AS-SET | Provider | Prefixes | Risk Level |
|--------|----------|----------|------------|
| **AS-HURRICANE** | Hurricane Electric | **411,327** | **CATASTROPHIC** |
| **AS-AMAZON** | Amazon | **18,547** | **MAJOR** |
| **AS-GOOGLE** | Google | **7,259** | **SIGNIFICANT** |
| AS-HETZNER | Hetzner | 4,804 | Large |
| AS-MICROSOFT | Microsoft | 1,406 | Medium |
| AS-FACEBOOK | Meta | 541 | Medium |
| AS-NFLX | Netflix | 67 | Small |

**Critical Example**: A malicious customer adding **AS-HURRICANE** (411,327 prefixes) to their AS-SET could leak Hurricane Electric's entire prefix database to thousands of peers. With member-of-as-set, AS-HURRICANE would be **pruned** (not authorized), preventing this catastrophic leak.

## Status

- [x] RFC Draft (RFCXML v3)
- [x] Implementation Guide
- [x] Working POC with real IRR data (AS-HURRICANE, AS-AMAZON, AS-GOOGLE)
- [ ] IETF GROW WG adoption
- [ ] Tool integration (bgpq4, IRRd)

## Requirements

- `bgpq4` - AS-SET expansion tool
- `whois` client - IRR queries
- Standard Unix tools (bash, grep, awk)

## Authors

- Saku Ytti (NTT Communications Corporation)
- Based on discussions in #networker IRC community

## License

See IETF Trust Legal Provisions for RFC documents.

## References

- RFC 2622: Routing Policy Specification Language (RPSL)
- RFC 6480: RPKI Infrastructure
- RFC 9595: BGP ASPA
