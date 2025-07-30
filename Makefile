default: dev

dev:
	fastapi dev src/main.py

run:
	fastapi run src/main.py

format:
	ruff format