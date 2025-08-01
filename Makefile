# Makefile vars are global
ifeq ($(OS),Windows_NT)
# windows-specific commands
	VENV_ACTIVATE_CMD = .venv\Scripts\activate.bat
	CLEAN_CMD = rmdir /s /q uploads
else
# unix-specific commands
	VENV_ACTIVATE_CMD = . .venv/bin/activate
	CLEAN_CMD = rm -rf uploads
endif


default: dev

dev:
	fastapi dev src/main.py

run:
	fastapi run src/main.py

venv:
	$(VENV_ACTIVATE_CMD)

# this is mostly cuz i forgor how to deactivate the venv sometimes lmao. probably not needed to do ever
venv-deactivate:
	deactivate

format:
	ruff format

# clean:
# 	$(CLEAN_CMD)