Feature: loader_node engine integration

## Files modified

- `src/domain/models/state/state.py`: Added WorkflowState-compatible fields (user_input, processing_state, current_node, result, errors) to AgentState so it is a superset usable by both old and new nodes.

- `src/infra/adapters/workflow/engine.py`: Switched StateGraph from WorkflowState to AgentState. Added node_loader_task import. Rewired graph: loader -> start -> process -> end, with loader as entry point. Updated execute_and_stream signature from WorkflowState to AgentState.

## Files verified (no changes needed)

- `src/infra/adapters/workflow/__init__.py`: Already exports node_loader_task.
- `src/domain/models/__init__.py`: Already exports AgentState.
