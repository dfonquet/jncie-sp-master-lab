# IS-IS Adjacency Failure

## Background

One core adjacency no longer forms after an unreviewed change.

## Requirements

Identify the fault, restore Level 2 adjacency without changing the addressing
plan, and prove IPv4/IPv6 loopback reachability.

## Restrictions

Do not disable authentication or replace IS-IS. Preserve all unaffected links.

## Success criteria

Both endpoint observations are Up, the Level 2 database is synchronized, and
the affected loopbacks are reachable. Suggested limit: 30 minutes; 10 points.
