# LOWCACHE profile drawing set.
#
# The sheets in assets/ are build output. Edit scripts/build_sheets.py (layout
# and copy) or scripts/drawset.py (primitives), then `make sheets`.

PY_ENV := python3.withPackages(p:[p.fonttools p.brotli])
NIXSH  := nix-shell -p '$(PY_ENV)' --run
PORT   ?= 8731

.PHONY: sheets avatar stats preview serve clean help

help:
	@echo 'make sheets   rebuild assets/*.svg from scripts/'
	@echo 'make avatar   rebuild assets/avatar.svg + .png (profile picture)'
	@echo 'make stats    refresh assets/stats.json from the GitHub API'
	@echo 'make preview  serve the repo and print the preview URL (PORT=$(PORT))'
	@echo 'make clean    drop __pycache__'

# Rebuilds every sheet. Fails loudly if any text overflows its box -- that is
# drawset.fit() doing its job, not a broken build.
sheets:
	$(NIXSH) 'python3 scripts/build_sheets.py'

# Emits both: the SVG is source of truth, the PNG is what GitHub accepts for an
# avatar upload (it rejects SVG). Rasterised through librsvg, not ImageMagick's
# internal renderer.
avatar:
	python3 scripts/build_avatar.py

stats:
	python3 scripts/gen-stats.py

# Checks the sheets through the same <img> path GitHub uses. Loading them as
# top-level documents is NOT a valid check: animation and external font loading
# behave differently there. See scripts/preview.html.
preview: serve

serve:
	@echo 'preview -> http://127.0.0.1:$(PORT)/scripts/preview.html'
	@python3 -m http.server $(PORT) --bind 127.0.0.1

clean:
	rm -rf scripts/__pycache__
