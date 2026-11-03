# Roadmap

## MVP

- [x] Separate CLI package and console entry point.
- [x] Generate projects from an immutable FastApiBackbone commit by default.
- [x] Rename the Python package and project metadata.
- [x] Include/exclude Docker assets.
- [x] Include/exclude Kubernetes/Kustomize assets.
- [x] Refuse to overwrite non-empty destinations.
- [x] Validate archive paths and extraction size.
- [ ] End-to-end generated-project CI against the pinned template.
- [ ] Publish the CLI package to PyPI.

## Next

- Add template compatibility metadata and a doctor command.
- Add offline template caching.
- Add selectable authentication and persistence profiles after defining supported combinations.
- Add generated-project smoke tests for Docker and Kubernetes options.
- Add release automation and signed artifacts.

## Design constraints

- FastApiBackbone remains the canonical backend source.
- Generated projects are independent directories with no inherited Git history.
- Pydantic remains in the backend; PydanticAI and Flutter are excluded.
- Template revisions are explicit and reproducible. The default is pinned to a commit SHA, not a moving branch.
