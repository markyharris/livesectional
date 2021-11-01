# Minimize Root Access

## Status

Accepted

## Context

Processes running as root have full access to the system, security vulnerabilities risk compromising the entire system.

## Decision

Web facing applications need to run as a non-priviliged user.
Actions that require root access should not be directly triggerable via web actions

## Consequences

The entire system will require more discrete components
Each individual component should be simpler - easier to debug; easier to secure
