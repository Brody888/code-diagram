.PHONY: setup index

PROJECT ?=

ifeq ($(PROJECT),)
  $(error USAGE: make setup PROJECT=/path/to/your-codebase)
endif

setup:
	@python3 setup.py $(PROJECT)

index:
	@python3 scripts/build-index-ts.py --project $(PROJECT)
