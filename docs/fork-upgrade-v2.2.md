# Updating this fork to the Eltako web panel

This branch integrates upstream tag `v2.2.1rc4`, a prerelease, into the
`runevh/home-assistant-eltako` fork. The panel depends on the v2 backend and
configuration model; it is not a standalone frontend that can be added to v1.

The previous fork commit, `b670080`, restored a working v1.5.10 installation.
Conflicts with that older architecture are resolved using the v2 implementations.
Upstream already includes the climate home/eco/sleep presets and priority select
controls. The older German getting-started documentation is retained, but use
the v2 migration guide for current setup instructions.

The integration requires `eltako14bus==1.0.1` and
`esp2-gateway-adapter==0.2.21`. Its admin-only ELTAKO sidebar panel provides
gateway/device setup, live telegrams, diagnostics, discovery and teach-in.
See [the web UI guide](web-ui/readme.md).

## Before deploying to the existing installation

Repository integration does not deploy files or restart Home Assistant.
Follow [the upstream migration guide](migration-v1-to-v2.2.md) before deployment:

1. Back up Home Assistant, the existing integration and Eltako configuration.
2. Preserve gateway IDs, device addresses, sender addresses and sender EEPs.
   Check entity identifiers and automation event names against v2; these are
   not all compatible with v1.
3. Check the existing YAML against the v2 schema. YAML-defined devices remain
   managed in YAML; panel edits do not override those declarations.
4. Install the complete integration and its declared dependencies, then restart.
5. Confirm panel access, gateway reception and one actuator's command/feedback
   path before testing the rest of the installation. Verify climate presets and
   priority controls as well as existing automations.

Do not start a bus scan or teach-in simply to verify that the panel loads: these
operations can lock the bus or change actuator configuration.
Upstream also schedules a first-time bus scan for a connected bus gateway whose
memory has never been scanned. Plan the initial deployment for an interruption
to bus control; opening the panel is not the only way a scan can start.

The existing USB disconnects are a separate unresolved issue. This update is not
evidence that the physical or virtualized USB connection has been repaired.

## Temporary live test, 2026-11-10

The panel registered at `/eltako` and its JavaScript returned HTTP 200 on
Home Assistant 2026.3.4. Gateway setup failed because the saved v1 description
contained `(Id: 1, BaseId: ...)`, which the v2 ID parser rejected. The test was
stopped and v1.5.10 restored, including the original registries. Integration and
configuration checksums matched the backup, and incoming bus messages resumed.

The ID parser now accepts both description formats, with regression tests.
A subsequent extended live test confirmed the parser fix and exposed two further
startup failures: an unsupported `via_device_id` DeviceInfo field on HA 2026.3.4,
and an omitted message delay passed as None into the serial library. Both were
fixed and deployed. The gateway reports connected and panel JavaScript returns
HTTP 200. The integration suite runs 1,607 tests successfully (one skipped).

The extended test was subsequently stopped and v1.5.10 restored after the owner
requested preservation of existing heating behavior. Heating feedback and priority
restoration were observed in the restored integration's logs.

A migration now translates v1 unique IDs before gateway platforms start, while
retaining existing entity IDs, registry identities and user settings. This covers
local and radio device addresses and suffixes. It checks all mappings for conflicts
before applying changes and refuses ambiguous duplicate entries rather than
silently choosing one. Repeated migration is a no-op.

An offline check using the actual Home Assistant 2026.3.4 registry and the owner's
285 Eltako identities preserved every entity ID and disabled setting. All four
heating targets referenced by the current automations resolve after migration.
Regression tests also verify that v2 registration reuses the original registry
entry rather than creating a duplicate. The migration is not yet deployed live.

Before leaving a future upgrade running, verify the original heating entities
are available, issue a temperature command and confirm actuator feedback, and
check priority/preset behavior and existing lighting/cover controls. A successful
registry migration alone does not prove physical control or USB reliability.
The pre-test backups remain at `/share/eltako-extended-test-20261110` on the host.

## Entity naming update, 2026-11-10

At the owner's request, the live v1 installation's 285 public entity IDs were
renamed from `eltako_gw1_...` to `eltako_gw_1_...`, together with references in
YAML automations/templates, stored dashboards, schedules and restore states.
Internal v1 unique IDs remain unchanged so v1 still resolves the same registry
entries; the v2 migration above will update those unique IDs later without
renaming the now-normalized public IDs. Registry identities and disabled states
are preserved. Historical logs and recorder data are not rewritten.
A separate consistent backup and mapping are retained on the host at
`/share/eltako-gw-rename-20261110`. Older rollback snapshots predate this rename
and must not be restored without also restoring their matching YAML/dashboard
references.

## Validation

CI runs the integration suite on Python 3.14 with both Home Assistant 2026.3.4
(the installed version when this update was prepared) and the current package.
The standalone tests must run separately because they install a Home Assistant
shim in their process.

Compatibility repairs on top of the tag synchronize the standalone version,
regenerate the panel's help index, restore missing cover/fan shim modules, and
convert numeric thermostat service parameters to the enums expected by the bus
library. Test fixtures use the new library's supported encoders and temperature
decoding behavior. Existing climate presets and priority controls remain part
of the upstream implementation.

```sh
python -m pip install -r requirements.txt 'homeassistant==2026.3.4'
ruff check custom_components tests
python -m unittest discover tests -v
python -m pytest eltako_standalone/tests
```

## Feature branch retest after entity renaming

The initial retest migrated all 285 registry entries and sent heating startup
commands, but a detected base ID of `00-00-00-60` replaced the configured address
and redirected feedback away from existing entity subscriptions. That test was
rolled back. A safeguard now retains an explicitly configured base ID when a
reported address disagrees; gateways with no configured address can still
learn one. The source of the conflicting hardware response remains unresolved.

The corrected branch was redeployed on 2026-11-10 and is running for manual
testing. All 285 original public entity IDs, registry identities and disabled
settings match the new backup; 11 additional diagnostic entities were created.
Panel JavaScript returns HTTP 200. Startup heating commands were sent, and
actuator feedback reached the four entities targeted by heating automations.
The suite runs 1,616 tests successfully (one skipped), and Ruff passes.

Manual panel interaction and physical setpoint/actuator confirmation remain
pending. Keep the PR in draft until these checks pass. This test's rollback
snapshot is `/share/eltako-feedback-retest-20261110`; it includes the renamed
`gw_1` configuration. The feature branch has not been merged.
