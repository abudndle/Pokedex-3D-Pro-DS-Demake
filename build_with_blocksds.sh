#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v make >/dev/null 2>&1; then
  echo 'ERROR: make is missing. Run this from Wonderful Toolchain Shell with BlocksDS installed.' >&2
  exit 1
fi
if [[ -f /opt/wonderful/bin/wf-env ]]; then
  source /opt/wonderful/bin/wf-env
fi
make verify-assets
make -j2
if [[ ! -s Pokedex3D_DS_BlocksDS.nds ]]; then
  echo 'ERROR: Build returned without a nonempty .nds file.' >&2
  exit 1
fi
printf 'ROM built: %s\n' "$(pwd)/Pokedex3D_DS_BlocksDS.nds"
