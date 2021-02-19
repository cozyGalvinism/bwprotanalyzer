VERSION := $(shell poetry version -s)

all: clean build

clean:
	rm -rf dist/

build:
	sed -i 's/\x27.*\x27/\x27$(VERSION)\x27/' bwprotanalyzer/__init__.py
	poetry build