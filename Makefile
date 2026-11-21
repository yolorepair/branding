# YOLO Electronics Repair brand asset Makefile
#
# Usage:
#   make            # build everything (SVG + PNG + favicon + tokens + BRANDING.md)
#   make svgs       # only SVGs
#   make pngs       # only PNGs
#   make favicons   # only favicons
#   make manifest   # only web manifest + maskable icons
#   make og         # only Open Graph / social-share cards
#   make tokens     # only brand tokens (brand.css + brand.json)
#   make docs       # only BRANDING.md
#   make clean      # remove all generated assets
#   make check      # CI check: exit 1 if BRANDING.md is out of sync
#   make install    # install Python dependencies
#
# The brand.toml file is the source of truth. Edit it, then run `make`.

PYTHON := python3
SCRIPTS := scripts

.PHONY: all build svgs pngs favicons manifest og tokens docs clean check install help

all: build docs

help:
	@echo "Targets:"
	@echo "  all      - build everything (default)"
	@echo "  build    - generate SVGs, PNGs, favicons, OG cards, and tokens"
	@echo "  svgs     - generate only SVGs"
	@echo "  pngs     - generate only PNGs"
	@echo "  favicons - generate only favicons"
	@echo "  manifest - generate web manifest + maskable icons"
	@echo "  og       - generate Open Graph / social-share cards"
	@echo "  tokens   - generate brand tokens (brand.css + brand.json)"
	@echo "  docs     - regenerate BRANDING.md tables from brand.toml"
	@echo "  clean    - remove all generated assets"
	@echo "  check    - verify BRANDING.md is in sync with brand.toml"
	@echo "  install  - install Python dependencies"

build:
	$(PYTHON) $(SCRIPTS)/build.py all

svgs:
	$(PYTHON) $(SCRIPTS)/build.py mark pulse wordmark lockup

pngs:
	$(PYTHON) $(SCRIPTS)/build.py png

favicons:
	$(PYTHON) $(SCRIPTS)/build.py favicon

manifest:
	$(PYTHON) $(SCRIPTS)/build.py manifest

og:
	$(PYTHON) $(SCRIPTS)/build.py og

tokens:
	$(PYTHON) $(SCRIPTS)/build.py tokens

docs:
	$(PYTHON) $(SCRIPTS)/render_branding_md.py

clean:
	$(PYTHON) $(SCRIPTS)/build.py --clean all

check:
	$(PYTHON) $(SCRIPTS)/render_branding_md.py --check

install:
	$(PYTHON) -m pip install -r requirements.txt
