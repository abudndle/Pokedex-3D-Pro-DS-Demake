# Native BlocksDS port build (C14 baseline, migration in progress)
export BLOCKSDS ?= /opt/blocksds/core
export BLOCKSDSEXT ?= /opt/blocksds/external
export WONDERFUL_TOOLCHAIN ?= /opt/wonderful
NAME := Pokedex3D_DS_BlocksDS
ARM_NONE_EABI_PATH ?= $(WONDERFUL_TOOLCHAIN)/toolchain/gcc-arm-none-eabi/bin/
CC := $(ARM_NONE_EABI_PATH)arm-none-eabi-gcc
NITROFSDIR ?= nitrofs
SOURCE_REQUIRED := main.c photo_album.c photo_viewer.c save_store.c ui_assets.c feature_menu.c move_dex.c challenge.c
MISSING := $(foreach f,$(SOURCE_REQUIRED),$(if $(wildcard source/$(f)),,source/$(f)))
.PHONY: all verify-source verify-assets clean
all: verify-source verify-assets
	@$(MAKE) -f Makefile.native rom
verify-source:
	@if [ -n "$(strip $(MISSING))" ]; then echo "ERROR: Native port source migration incomplete. Missing: $(MISSING)" >&2; exit 1; fi
verify-assets:
	@test -d "$(NITROFSDIR)" || { echo "ERROR: Private original-asset NitroFS directory missing: $(NITROFSDIR)" >&2; exit 1; }
clean:
	@rm -rf build Pokedex3D_DS_BlocksDS.nds

# Asset-free native compilation smoke test; never treated as a release ROM.
.PHONY: dev-rom
dev-rom:
	@$(MAKE) -f Makefile.native NITROFSDIR= rom

# Run portable host-side regression tests without Docker, assets, or Actions.
# DS-Homebrew builds similarly keep development tooling reproducible locally.
.PHONY: check-host
check-host:
	@sh tests/run_source_smoke.sh
	@python3 -m unittest discover -s tests -p 'test_asset_manifest*.py'
