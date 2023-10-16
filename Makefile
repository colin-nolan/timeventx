MARKDOWN_FILES := $(shell find . -type f -name '*.md' ! -path '*/site-packages/*' ! -path '*build/*' ! -path '*/node_modules/*' ! -path '*/.venv/*' ! -path '*/.pytest_cache/*')

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

build-backend:
	./scripts/build-backend.sh $(ARCH)

build-frontend: .must_have_api_server_location
	./scripts/build-frontend.sh $(API_SERVER_LOCATION)

fmt: format

format: format-frontend format-backend format-markdown

format-frontend:
	prettier_check_flag=$(if $(filter true,$(CHECK)),--check,--write); \
	cd frontend; \
	yarn run prettier $${prettier_check_flag} .

format-backend:
	poetry_check_flag=$(if $(filter true,$(CHECK)),--check,); \
	cd backend; \
	poetry run black $${poetry_check_flag} timeventx; \
	poetry run isort $${poetry_check_flag} timeventx

format-markdown:
	mdformat_check_flag=$(if $(filter true,$(CHECK)),--check,); \
	mdformat $${mdformat_check_flag} $(MARKDOWN_FILES)

test: test-backend test-frontend

test-backend: test-backend-unit

test-backend-unit:
	cd backend; \
	coverage run --concurrency=multiprocessing -m pytest

test-frontend: test-frontend-unit test-frontend-system

test-frontend-unit:
	cd frontend; \
	yarn run test-unit

test-frontend-system:
	cd frontend; \
	yarn run test-system; \
	yarn nyc report --reporter=lcov

.PHONY: all build build-frontend build-backend fmt format format-backend format-markdown test test-backend test-backend-unit test-frontend test-frontend-unit test-frontend-system
