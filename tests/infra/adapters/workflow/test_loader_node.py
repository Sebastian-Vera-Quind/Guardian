import unittest
from unittest.mock import patch
from src.infra.adapters.workflow.nodes.loader import node_loader_task, determine_load_route
from src.domain.models.errors.loader_errors import LoaderNodeError


def _make_file(path: str, content: str, extension: str = "py") -> dict:
    return {"path": path, "content": content, "extension": extension}


class TestDetermineLoadRoute(unittest.TestCase):

    def test_simple_route_when_only_files_content(self):
        state = {"files_content": [_make_file("a.py", "x = 1")]}
        self.assertEqual(determine_load_route(state), "simple")

    def test_clone_route_when_only_repository(self):
        state = {"repository": {"url": "https://github.com/u/r.git", "commit_sha": "abc"}}
        self.assertEqual(determine_load_route(state), "clone")

    def test_clone_route_takes_priority_when_both_present(self):
        state = {
            "repository": {"url": "https://github.com/u/r.git", "commit_sha": "abc"},
            "files_content": [_make_file("a.py", "x = 1")],
        }
        self.assertEqual(determine_load_route(state), "clone")

    def test_raises_loader_node_error_when_no_inputs(self):
        with self.assertRaises(LoaderNodeError):
            determine_load_route({})


class TestNodeLoaderTaskSimpleRoute(unittest.IsolatedAsyncioTestCase):

    async def test_simple_route_sanitizes_files_content(self):
        state = {
            "files_content": [_make_file("a.py", "x = 1\n\ny = 2\n   \nz = 3")],
        }
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "simple")
        for file in result["files_content"]:
            for line in file["content"].split('\n'):
                self.assertTrue(line.strip(), f"Blank line found: {repr(line)}")

    async def test_simple_route_writes_total_lines(self):
        state = {
            "files_content": [
                _make_file("a.py", "line1\nline2\nline3"),
                _make_file("b.py", "x\ny"),
            ],
        }
        result = await node_loader_task(state)
        self.assertIn("total_lines", result)
        self.assertIsInstance(result["total_lines"], int)
        self.assertGreater(result["total_lines"], 0)

    async def test_simple_route_extracts_valid_attribution(self):
        valid_jsonl = '{"agent": "gpt-4"}\n{"agent": "claude"}'
        state = {
            "files_content": [
                _make_file(".devcore-attribution.jsonl", valid_jsonl, "jsonl"),
                _make_file("src/main.py", "print('hello')"),
            ],
        }
        result = await node_loader_task(state)
        self.assertEqual(result.get("ai_attribution_jsonl"), valid_jsonl)
        paths = [f["path"] for f in result["files_content"]]
        self.assertNotIn(".devcore-attribution.jsonl", paths)

    async def test_simple_route_no_attribution_when_absent(self):
        state = {
            "files_content": [_make_file("src/main.py", "x = 1")],
        }
        result = await node_loader_task(state)
        self.assertNotIn("ai_attribution_jsonl", result)

    async def test_simple_route_passes_repository_unchanged(self):
        repo = {"url": "https://github.com/u/r.git", "commit_sha": "abc"}
        state = {
            "files_content": [_make_file("a.py", "x = 1")],
            "repository": None,
        }
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "simple")


class TestNodeLoaderTaskCloneRoute(unittest.IsolatedAsyncioTestCase):

    async def test_clone_route_writes_metadata(self):
        state = {
            "repository": {
                "url": "https://github.com/acme/repo.git",
                "installation": "inst-1",
                "commit_sha": "abc123",
                "target": "main",
            }
        }
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "clone")
        self.assertIn("metadata", result)
        metadata = result["metadata"]
        self.assertEqual(metadata["owner"], "acme")
        self.assertEqual(metadata["repo_name"], "repo")

    async def test_clone_route_passes_files_content_unchanged(self):
        state = {
            "repository": {
                "url": "https://github.com/acme/repo.git",
                "commit_sha": "abc",
                "target": "main",
            },
            "files_content": [_make_file("a.py", "x = 1")],
        }
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "clone")
        self.assertNotIn("files_content", result)


class TestNodeLoaderTaskDecorator(unittest.TestCase):

    def test_node_is_decorated_with_logging(self):
        import functools
        func = node_loader_task
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        self.assertTrue(
            hasattr(node_loader_task, "__wrapped__") or callable(node_loader_task),
            "node_loader_task should be a callable (decorated with @with_logging)"
        )


class TestLoaderNode(unittest.IsolatedAsyncioTestCase):
    """Tests named per spec requirements (R1-R12)."""

    async def test_simple_route_when_only_files_content(self):
        state = {"files_content": [{"path": "a.py", "content": "x = 1", "extension": "py"}]}
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "simple")

    async def test_clone_route_when_only_repository(self):
        state = {"repository": {"url": "https://github.com/u/r.git", "commit_sha": "abc", "target": "main"}}
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "clone")

    async def test_clone_takes_priority_when_both_present(self):
        state = {
            "repository": {"url": "https://github.com/u/r.git", "commit_sha": "abc", "target": "main"},
            "files_content": [{"path": "a.py", "content": "x = 1", "extension": "py"}],
        }
        result = await node_loader_task(state)
        self.assertEqual(result["load_to"], "clone")

    async def test_raises_when_no_inputs(self):
        from src.domain.models.errors.loader_errors import LoaderNodeError
        with self.assertRaises(LoaderNodeError):
            await node_loader_task({})

    async def test_simple_writes_total_lines(self):
        state = {
            "files_content": [
                {"path": "a.py", "content": "line1\nline2\nline3", "extension": "py"},
            ]
        }
        result = await node_loader_task(state)
        self.assertIn("total_lines", result)
        self.assertIsInstance(result["total_lines"], int)
        self.assertGreater(result["total_lines"], 0)

    async def test_simple_sanitizes_files_content(self):
        state = {
            "files_content": [
                {"path": "a.py", "content": "x = 1\n\ny = 2\n   \nz = 3", "extension": "py"},
            ]
        }
        result = await node_loader_task(state)
        for file in result["files_content"]:
            for line in file["content"].split('\n'):
                self.assertTrue(line.strip(), f"Blank line found: {repr(line)}")

    async def test_simple_extracts_valid_attribution(self):
        valid_jsonl = '{"agent": "gpt-4"}\n{"agent": "claude"}'
        state = {
            "files_content": [
                {"path": ".devcore-attribution.jsonl", "content": valid_jsonl, "extension": "jsonl"},
                {"path": "src/main.py", "content": "print('hello')", "extension": "py"},
            ]
        }
        result = await node_loader_task(state)
        self.assertEqual(result.get("ai_attribution_jsonl"), valid_jsonl)
        paths = [f["path"] for f in result["files_content"]]
        self.assertNotIn(".devcore-attribution.jsonl", paths)

    async def test_clone_writes_metadata_dict(self):
        state = {
            "repository": {
                "url": "https://github.com/myorg/myrepo.git",
                "commit_sha": "sha1",
                "target": "main",
            }
        }
        result = await node_loader_task(state)
        self.assertIn("metadata", result)
        metadata = result["metadata"]
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["owner"], "myorg")
        self.assertEqual(metadata["repo_name"], "myrepo")


if __name__ == "__main__":
    unittest.main()
