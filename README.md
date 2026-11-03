# FastApiBackbone CLI

[![CI](https://github.com/safuh/FastApiBackbone-CLI/actions/workflows/ci.yml/badge.svg)](https://github.com/safuh/FastApiBackbone-CLI/actions/workflows/ci.yml)

A command-line project generator for creating independent backend services from the canonical [FastApiBackbone](https://github.com/safuh/FastApiBackbone) foundation.

It preserves **FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, and the authentication primitives** in the source foundation. It does not add PydanticAI or Flutter.

## Install for development

Python 3.11+ is required.

```bash
git clone https://github.com/safuh/FastApiBackbone-CLI.git
cd FastApiBackbone-CLI
pip install -e ".[dev]"
```

## Generate a project

```bash
# Docker included by default; Kubernetes omitted by default
fastapi-backbone create inventory-api

# Choose output directory and include Kubernetes/Kustomize
fastapi-backbone create billing-api --output ./services --kubernetes

# Exclude Docker assets
fastapi-backbone create reporting-api --no-docker

# Pin a different source revision
fastapi-backbone create warehouse-api --template-ref <tag-or-commit>
```

The default template is pinned to FastApiBackbone commit:

`89832bc467d21453e73f2e822cae4224d0c5a955`

A generated project receives its own Python package name, application display name, README, and project metadata. It is copied as a standalone directory without the source repository's Git history.

## Generated project contents

- FastAPI application factory and API routes.
- Pydantic Settings and environment profiles.
- Async SQLAlchemy engine, sessions, repositories, and Unit of Work.
- Alembic migration environment.
- PostgreSQL production support and SQLite development/test support.
- Health and readiness endpoints, structured logging, request context middleware.
- Password/JWT authentication primitives.
- Tests and developer tooling.
- Optional Docker/Compose and Kubernetes/Kustomize deployment assets.

## Commands

```bash
fastapi-backbone create <project-name>
fastapi-backbone features
fastapi-backbone version
```

Use `fastapi-backbone create --help` for options.

## Template and network behavior

The CLI downloads a GitHub source archive at generation time. The default is an immutable commit SHA for reproducibility. A different branch, tag, or commit can be supplied with `--template-ref`. The archive is size-limited and checked for unsafe paths and links before extraction.

Generation requires network access to GitHub. Offline template caching is planned but is not part of the initial MVP.

## Development checks

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

## Project principles

- FastApiBackbone remains the canonical backend foundation.
- Generated projects are independent and own their Git history.
- Pydantic remains; PydanticAI and Flutter are excluded.
- Generated projects must not overwrite a non-empty destination.
- Template revisions must be reproducible.
