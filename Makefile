default: dev

dev:
	fastapi dev src/main.py

run:
	fastapi run src/main.py

venv:
	source .venv/bin/activate

format:
	ruff format