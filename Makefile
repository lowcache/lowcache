# LOWCACHE profile drawing set.
#
# The sheets in assets/ are build output. Edit scripts/build_sheets.py (layout
# and copy) or scripts/drawset.py (primitives), then `make sheets`.

PY_ENV := python3.withPackages(p:[p.fonttools p.brotli])
NIXSH  := nix-shell -p '$(PY_ENV)' --run
PORT   ?= 8731

.PHONY: sheets stats preview serve clean help

help:
	@echo 'make sheets   rebuild assets/*.svg from scripts/'
	@echo 'make stats    regenerate assets/stats.svg from the GitHub API'
	@echo 'make preview  serve the repo and print the preview URL (PORT=$(PORT))'
	@echo 'make clean    drop __pycache__'

# Rebuilds every sheet. Fails loudly if any text overflows its box -- that is
# drawset.fit() doing its job, not a broken build.
sheets:
	$(NIXSH) 'python3 scripts/build_sheets.py'

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
