#!/usr/bin/env bash
# C274: real DeSmuME test of a C272-built diagnostic ROM with SYNTHETIC geometry.
# No original Nintendo assets, private user data, ROMs, or frames leave this job.
set -euo pipefail
root="$(mktemp -d /tmp/c274-XXXXXXXX)"
chmod 700 "$root"
cleanup() {
  rm -f c251-home.xwd c251-mapped.xwd c251-unmapped.xwd c251-back.xwd
  sudo rm -rf -- "$root"
}
trap cleanup EXIT
python3 tests/c251_synthetic_rom_stage.py "$root"
test -s "$root/staged/C249_PRIVATE_DIAGNOSTIC_REPORT.json"
# BlocksDS slim does not ship Python; install it inside the disposable image.
# Only /private receives the synthetic diagnostic ROM. The public checkout
# is mounted read-only, and the container does not upload any artifacts.
docker run --rm \
  -v "$PWD:/work:ro" -v "$root:/private" -w /work \
  skylyrac/blocksds:slim-latest sh -ec '
    apt-get update -qq
    apt-get install -y python3 >/dev/null
    python3 tools/c272_private_rom_build.py \
      --stage /private/staged --output /private/output
  '
# The private builder creates 0700 directories and 0600 files owned by
# container root. Transfer ownership BEFORE even trying to stat the ROM.
# Only this disposable runner user may read the temporary diagnostic output.
sudo chown -R "$(id -u):$(id -g)" "$root/output"
rom="$root/output/C272_PRIVATE_DIAGNOSTIC.nds"
test -s "$rom"
test "$(stat -c %a "$rom")" = 600
python3 tests/verify_nds_rom.py "$rom"
python3 tools/verify_nds_rom.py "$rom"
test ! -e "$root/output/nitrofs/C249_PRIVATE_DIAGNOSTIC_REPORT.json"
# Exercise actual DS key events and both screens, not just ROM boot.
xvfb-run -a -s '-screen 0 1024x768x24' timeout 70s \
  bash tests/run_c251_synthetic_geometry_emulator.sh "$rom"
echo "C274 PASS: C249 synthetic stage -> C272 isolated ROM -> real DeSmuME A/Right/B"
echo "C274 is synthetic-only; original p200 asset rendering, melonDS and DSi remain unverified."
