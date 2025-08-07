# Makefile vars are global
ifeq ($(OS),Windows_NT)
# windows-specific commands
	CLEAN_CMD = rmdir /s /q uploads
else
# unix-specific commands
	CLEAN_CMD = rm -rf uploads
endif


default: dev

dev:
	fastapi dev src/main.py

run:
	fastapi run src/main.py

format:
	ruff format

# clean:
# 	$(CLEAN_CMD)

# venv:
# for windows: .venv\Scripts\activate
# for unix: . .venv/bin/activate

# this is mostly cuz i forgor how to deactivate the venv sometimes lmao. probably not needed to do ever
# venv-deactivate:
# 	.venv\Scripts\deactivate
