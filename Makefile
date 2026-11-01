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
	@python3 tools/check_private_release_assets.py --root "$(NITROFSDIR)" --release
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
	@set -eu; for test in \
		run_source_smoke.sh run_preview_stream_fixture.sh run_c104_original_ui_pages.sh run_c107_native_texture_alpha.sh run_c108_material_binding.sh run_c109_original_material_refs.sh run_c110_shader_caps.sh run_c118_title_audio.sh \
		run_menu_layout_smoke.sh run_dsi_feature_gating.sh \
		run_feature_menu_smoke.sh run_save_store_smoke.sh run_c119_resume_idle.sh run_c121_deep_resume.sh run_c122_navigation_resume.sh run_c123_resume_integrity.sh \
		run_challenge_smoke.sh run_move_dex_smoke.sh \
		run_c100_move_effect_view.sh \
		run_photo_album_smoke.sh run_custom_images.sh \
		run_bmp_loader.sh run_image_background.sh \
		run_settings_images.sh run_menu_navigation.sh run_c123_home_hotspots.sh \
		run_game_save_bridge.sh run_c81_records_smoke.sh \
		run_c82_dex_search.sh run_c83_search_touch.sh; do \
		echo "Running $$test"; sh "tests/$$test"; \
	done
	@python3 -m unittest discover -s tests -p 'test_asset_manifest.py' -v
	@python3 -m unittest discover -s tests -p 'test_inspect_ds3m.py' -v
	@python3 tests/test_private_ui_packager.py
	@tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		cc -std=c11 -Wall -Wextra -Werror -Isource \
		tests/test_save_recovery.c source/save_store.c -o "$$tmp"; "$$tmp"

	@python3 -m unittest discover -s tests -p 'test_c76_model_texture_catalog_host.py' -v
	@python3 -m unittest discover -s tests -p 'test_c78_texture_loader_host.py' -v
	@python3 -m unittest discover -s tests -p 'test_c79_private_texture_manifest_builder.py' -v
	@python3 -m unittest discover -s tests -p 'test_c85_private_release_assets.py' -v
	@python3 -m unittest discover -s tests -p 'test_c132_private_recovery_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c133_c56_decoder.py' -v
	@python3 -m unittest discover -s tests -p 'test_c134_c56_geometry_bridge.py' -v
	@python3 -m unittest discover -s tests -p 'test_c135_missing_previews.py' -v
	@python3 -m unittest discover -s tests -p 'test_c136_native_uv_stage.py' -v
	@python3 -m unittest discover -s tests -p 'test_c86_preview_bundle_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c87_original_material_declaration_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c88_original_material_references.py' -v
	@python3 -m unittest discover -s tests -p 'test_c89_mesh_descriptor_join_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c90_original_draw_material_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c91_color_name_vram_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c92_diagnostic_textured_preview_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c93_private_browser_bundle_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c94_original_obj_uv_alignment.py' -v
	@python3 -m unittest discover -s tests -p 'test_c96_native_chunk_stream.py' -v
	@python3 -m unittest discover -s tests -p 'test_c98_private_geometry_qa_nitrofs.py' -v
	@python3 -m unittest discover -s tests -p 'test_c99_linux_visual_evidence_audit.py' -v
	@python3 -m unittest discover -s tests -p 'test_c97_batched_chunk_io.py' -v
	@python3 -m unittest discover -s tests -p 'test_c102_original_audio_source_recovery.py' -v
	@python3 -m unittest discover -s tests -p 'test_c103_original_cwav_dsp_to_pcm.py' -v
	@python3 -m unittest discover -s tests -p 'test_c110_original_shader_capabilities.py' -v
	@python3 -m unittest discover -s tests -p 'test_c111_original_sampler_evidence.py' -v
	@python3 -m unittest discover -s tests -p 'test_c113_private_material_words.py' -v
	@python3 -m unittest discover -s tests -p 'test_c114_crossfile_source_consistency.py' -v
	@python3 -m unittest discover -s tests -p 'test_c114_original_sampler_differential.py' -v
	@python3 -m unittest discover -s tests -p 'test_c80_feature_parity.py' -v
