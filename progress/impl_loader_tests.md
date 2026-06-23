# impl_loader_tests — feature loader_node (T10, T11)

## Tests escritos

### T10: GithubMetadataReader
File: `tests/infra/adapters/github/test_metadata_reader.py`

All `__init__.py` confirmed present:
- `tests/infra/__init__.py`
- `tests/infra/adapters/__init__.py`
- `tests/infra/adapters/github/__init__.py`

Two test classes:

**TestGithubMetadataReaderExtractFromRepository** (pre-existing, extended):
- `test_extract_from_repository_parses_owner_from_url`
- `test_extract_from_repository_parses_repo_name_from_url`
- `test_extract_from_repository_maps_target_to_branch`
- `test_extract_from_repository_copies_commit_sha`
- `test_extract_from_repository_uses_default_author_name`
- `test_extract_from_repository_uses_provided_author_name`
- `test_extract_from_repository_returns_repository_metadata_instance`
- `test_extract_from_repository_commit_message_is_none` (added)

**TestGithubMetadataReaderSpecNames** (added — canonical spec names):
- `test_extract_owner_from_github_url` — URL `https://github.com/myorg/myrepo.git` → owner=`myorg`
- `test_extract_repo_name_from_github_url` — same URL → repo_name=`myrepo`
- `test_maps_target_to_branch` — `target="develop"` → `branch=="develop"`
- `test_commit_sha_is_copied` — commit_sha propagated verbatim
- `test_default_author_name_when_missing` — no `author_name` key → `"Unknown Author"`
- `test_uses_provided_author_name` — explicit `author_name` used
- `test_returns_repository_metadata_instance` — return type is `RepositoryMetadata`
- `test_commit_message_is_none` — `commit_message` is always `None` (no GitHub API)

### T11: node_loader_task
File: `tests/infra/adapters/workflow/test_loader_node.py`

All `__init__.py` confirmed present:
- `tests/infra/adapters/workflow/__init__.py`

Four test classes (pre-existing extended with new `TestLoaderNode`):

**TestDetermineLoadRoute** (pre-existing, sync):
- `test_simple_route_when_only_files_content`
- `test_clone_route_when_only_repository`
- `test_clone_route_takes_priority_when_both_present`
- `test_raises_loader_node_error_when_no_inputs`

**TestNodeLoaderTaskSimpleRoute** (pre-existing, async):
- `test_simple_route_sanitizes_files_content`
- `test_simple_route_writes_total_lines`
- `test_simple_route_extracts_valid_attribution`
- `test_simple_route_no_attribution_when_absent`
- `test_simple_route_passes_repository_unchanged`

**TestNodeLoaderTaskCloneRoute** (pre-existing, async):
- `test_clone_route_writes_metadata`
- `test_clone_route_passes_files_content_unchanged`
- `test_clone_route_metadata_extraction_error_propagates`

**TestLoaderNode** (added — canonical spec names, IsolatedAsyncioTestCase):
- `test_simple_route_when_only_files_content` — R1
- `test_clone_route_when_only_repository` — R2
- `test_clone_takes_priority_when_both_present` — R3
- `test_raises_when_no_inputs` — R12
- `test_simple_writes_total_lines` — R6
- `test_simple_sanitizes_files_content` — R4, R5
- `test_simple_extracts_valid_attribution` — R8
- `test_clone_writes_metadata_dict` — R7
- `test_clone_metadata_extraction_failure_raises` — R9 (patch on GithubMetadataReader)

## Mapa R → test

| Req | Test |
|-----|------|
| R1 (files_content → load_to=simple) | `TestLoaderNode.test_simple_route_when_only_files_content` |
| R2 (repository → load_to=clone) | `TestLoaderNode.test_clone_route_when_only_repository` |
| R3 (clone priority when both) | `TestLoaderNode.test_clone_takes_priority_when_both_present` |
| R4 (sanitize files_content) | `TestLoaderNode.test_simple_sanitizes_files_content` |
| R5 (remove blank lines/empty files) | `TestLoaderNode.test_simple_sanitizes_files_content` |
| R6 (total_lines written) | `TestLoaderNode.test_simple_writes_total_lines` |
| R7 (metadata dict with owner+repo_name) | `TestLoaderNode.test_clone_writes_metadata_dict` |
| R8 (attribution extracted when valid jsonl) | `TestLoaderNode.test_simple_extracts_valid_attribution` |
| R9 (MetadataExtractionError on failure) | `TestLoaderNode.test_clone_metadata_extraction_failure_raises` |
| R12 (LoaderNodeError when no inputs) | `TestLoaderNode.test_raises_when_no_inputs` |

## Directorios verificados

All `__init__.py` were already present — no new ones needed to be created.
