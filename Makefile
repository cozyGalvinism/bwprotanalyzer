all: clean build-poetry

clean:
	rm -rf dist/

build-poetry:
	poetry build

build:
	cp bwprotanalyzer/__main__.py bin/bwprotanalyzer
	chmod +x bin/bwprotanalyzer
	poetry build
	tar -xvf dist/*.tar.gz --wildcards --no-anchored '*/setup.py' --strip=1
	rm -rf dist/*
	sed -i '/\x27python_requires\x27: .*,$$/a \ \ \ \ \x27entry_points:scripts\x27: [\x27bin/bwprotanalyzer\x27],' setup.py
	poetry run pip wheel --wheel-dir=dist/ .
	poetry run python setup.py sdist