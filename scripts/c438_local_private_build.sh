#!/usr/bin/env bash
# C438 — one-command LOCAL private original-asset build.
# Run only on an owner-controlled machine. Never commit, upload, or paste the
# resulting ROM, NitroFS stage, or reports. Output stays under ./private/.
set -Eeuo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: scripts/c438_local_private_build.sh --nitrofs-zip PATH [options]

Required:
  --nitrofs-zip PATH   Authorized local private NitroFS package (.zip)

Options:
  --manifest PATH      p3d-ds-original-assets-v1 manifest to validate first
  --asset-root PATH    NitroFS root that --manifest paths are relative to
                       (required together with --manifest)
  --stage-dir PATH     Stage directory (default: private/c137_nitrofs_stage)
  --skip-host-tests    Skip `make check-host`
  -h, --help           Show this help

Steps: toolchain check -> host tests -> optional manifest validation ->
       `make private-qa-rom` (preflight, stage, BlocksDS build) -> report.
USAGE
}

ZIP=""; MANIFEST=""; ASSET_ROOT=""; STAGE="private/c137_nitrofs_stage"; RUN_TESTS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --nitrofs-zip) ZIP="${2:-}"; shift 2 ;;
    --manifest) MANIFEST="${2:-}"; shift 2 ;;
    --asset-root) ASSET_ROOT="${2:-}"; shift 2 ;;
    --stage-dir) STAGE="${2:-}"; shift 2 ;;
    --skip-host-tests) RUN_TESTS=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$ZIP" ]]; then echo "ERROR: --nitrofs-zip is required" >&2; usage; exit 2; fi
if [[ -n "$MANIFEST" && -z "$ASSET_ROOT" ]]; then
  echo "ERROR: --manifest requires --asset-root" >&2; exit 2
fi
if [[ ! -f "$ZIP" ]]; then echo "ERROR: private package not found: $ZIP" >&2; exit 2; fi
if [[ -n "$MANIFEST" && ! -f "$MANIFEST" ]]; then echo "ERROR: manifest not found: $MANIFEST" >&2; exit 2; fi

cd "$(dirname "$0")/.."

if [[ -f /opt/wonderful/bin/wf-env ]]; then
  # shellcheck disable=SC1091
  source /opt/wonderful/bin/wf-env
fi
ARM_GCC="${WONDERFUL_TOOLCHAIN:-/opt/wonderful}/toolchain/gcc-arm-none-eabi/bin/arm-none-eabi-gcc"
if [[ ! -x "$ARM_GCC" ]]; then
  echo "BLOCKED: BlocksDS/Wonderful ARM compiler not found at $ARM_GCC" >&2
  echo "See https://blocksds.skylyrac.net/docs/setup/linux/" >&2
  exit 3
fi
command -v make >/dev/null || { echo "ERROR: make is missing" >&2; exit 3; }
command -v python3 >/dev/null || { echo "ERROR: python3 is missing" >&2; exit 3; }

mkdir -p private/reports

if [[ "$RUN_TESTS" -eq 1 ]]; then
  echo "== [1/3] host tests"
  make check-host
fi

if [[ -n "$MANIFEST" ]]; then
  echo "== [2/3] original-asset manifest validation"
  python3 tools/validate_original_assets.py --manifest "$MANIFEST" --root "$ASSET_ROOT"
else
  echo "== [2/3] manifest validation skipped (no --manifest given)"
fi

echo "== [3/3] private QA ROM build"
make private-qa-rom PRIVATE_NITROFS_ZIP="$ZIP" PRIVATE_NITROFS_STAGE="$STAGE"

ROM="Pokedex3D_DS_BlocksDS.nds"
if [[ ! -s "$ROM" ]]; then
  echo "ERROR: build finished without a nonempty $ROM" >&2; exit 1
fi
SHA="$(sha256sum "$ROM" | cut -d' ' -f1)"
printf '{"rom":"%s","sha256":"%s","fidelity_verified":false}\n' "$ROM" "$SHA" \
  > private/reports/C438_LOCAL_BUILD.json
echo "Built (local only, fidelity NOT verified): $(pwd)/$ROM"
echo "sha256: $SHA"
echo "Next: boot-test in melonDS and run the emulator gates under tools/. Do not share the ROM."
