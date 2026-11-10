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

The existing USB disconnects are a separate unresolved issue. This update is not
evidence that the physical or virtualized USB connection has been repaired.

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
