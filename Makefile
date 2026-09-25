PYTHON ?= $(shell if [ -f /home/unbinder/projects/shared_venv/bin/python3 ]; then echo /home/unbinder/projects/shared_venv/bin/python3; else echo python3; fi)

.PHONY: all check figures pdf hashes clean

all: check figures pdf hashes

check:
	$(PYTHON) scripts/check_release.py

figures:
	$(PYTHON) scripts/make_publication_figures.py

pdf: figures
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

hashes:
	find main.tex references.bib scripts data figures reproducibility -type f -print0 | sort -z | xargs -0 sha256sum > reproducibility/SHA256SUMS.txt

clean:
	rm -f main.aux main.bbl main.blg main.log main.out

