MARKDOWN_FILES := $(shell find . -type f -name '*.md' ! -path '*/site-packages/*' ! -path '*build/*' ! -path '*/node_modules/*')

ARCH ?= any

CHECK := false

SHELL := /bin/bash
.SHELLFLAGS := -euf -o pipefail -c

all: build

.must_have_api_server_location:
ifndef API_SERVER_LOCATION
	$(error API_SERVER_LOCATION must be set)
endif

build: .must_have_api_server_location
	@# XXX: it would be more idomatic if build was composed of `build-frontend` and `build-backend`
	./scripts/build.sh $(API_SERVER_LOCATION) $(ARCH)

build-frontend: .must_have_api_server_location
	./scripts/build-frontend.sh $(API_SERVER_LOCATION)

build-backend:
	./scripts/build-backend.sh $(ARCH)

fmt: format

format: format-backend	

format-backend:
	poetry_check_flag=$(if $(filter true,$(CHECK)),--check,); \
	cd backend; \
	poetry run black $${poetry_check_flag} garden_water; \
	poetry run isort $${poetry_check_flag} garden_water

format-markdown:
	mdformat_check_flag=$(if $(filter true,$(CHECK)),--check,); \
	mdformat $${mdformat_check_flag} $(MARKDOWN_FILES)

test: test-backend

test-backend:
	cd backend; \
	poetry run pytest

.PHONY: all build build-frontend build-backend fmt format format-backend format-markdown test test-backend
