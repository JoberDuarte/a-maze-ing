PYTHON=python3

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install flake8 mypy pytest build

run:
	$(PYTHON) a_maze_ing.py config_default.txt

debug:
	$(PYTHON) -m pdb a_maze_ing.py config_default.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf dist build *.egg-info

lint:
	# Run linters only on the project's source files to avoid analyzing site-packages
	flake8 a_maze_ing.py maze/
	mypy a_maze_ing.py maze/ --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 a_maze_ing.py maze/
	mypy a_maze_ing.py maze/ --strict
