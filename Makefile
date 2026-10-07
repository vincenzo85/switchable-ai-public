PYTHON ?= .venv/bin/python
PYTEST ?= $(PYTHON) -m pytest

.PHONY: help setup check test lint-architecture architecture mutation deck deck-backup numbers clean-artifacts

help:
	@printf "switchable_ai:\n"
	@printf "  make setup              crea .venv e installa le dipendenze\n"
	@printf "  make check              test + confini esagonali\n"
	@printf "  make mutation           mutation testing (i test devono mordere)\n"
	@printf "  make numbers            rigenera talk/numbers.json dai benchmark\n"
	@printf "  make deck               build del deck 3D (talk/deck/dist)\n"
	@printf "  make deck-backup        screenshot di ogni step + PDF di riserva (talk/screens)\n"

setup:
	python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'

check:
	$(PYTEST)
	$(PYTEST) -q tests/test_architecture_boundaries.py

test: check

lint-architecture:
	$(PYTEST) -q tests/test_architecture_boundaries.py

architecture: lint-architecture

mutation:
	$(PYTHON) tools/mutation_check.py

numbers:
	$(PYTHON) benchmarks/build_numbers.py

deck: numbers
	$(PYTHON) talk/deck/build.py

deck-backup: deck
	$(PYTHON) tools/deck_screens.py && $(PYTHON) tools/deck_pdf.py

clean-artifacts:
	find . -type d -name "__pycache__" -not -path "./.venv*" -exec rm -rf {} +
	rm -rf .pytest_cache
