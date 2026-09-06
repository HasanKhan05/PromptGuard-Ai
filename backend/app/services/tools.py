from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ToolRequest:
    tool_name: str
    resource_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolAuthorizationDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ToolExecutionResult:
    allowed: bool
    reason: str
    data: dict[str, Any] | None = None


@dataclass(frozen=True)
class ToolPolicy:
    allowed_resources: frozenset[str]
    parameter_validators: Mapping[str, Callable[[Any], bool]]


_PROJECTS = {
    "demo-api": {
        "project_id": "demo-api",
        "name": "PromptGuard Demo API",
        "summary": "Local read-only sample project for research tool authorization.",
    }
}
_ISSUES = {
    "issue-101": {
        "issue_id": "issue-101",
        "project_id": "demo-api",
        "title": "Validate request payloads",
        "status": "open",
    }
}
_FILES = {
    "src/app.py": {
        "file_id": "src/app.py",
        "summary": "FastAPI application entry point.",
        "symbols": ["app", "lifespan"],
    }
}

TOOL_POLICIES = {
    "get_project_info": ToolPolicy(frozenset(_PROJECTS), {}),
    "read_issue": ToolPolicy(frozenset(_ISSUES), {}),
    "get_file_summary": ToolPolicy(
        frozenset(_FILES),
        {"include_symbols": lambda value: isinstance(value, bool)},
    ),
}

READ_ONLY_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_info",
            "description": "Read local sample project metadata.",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "string", "enum": ["demo-api"]}},
                "required": ["project_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_issue",
            "description": "Read one local sample issue.",
            "parameters": {
                "type": "object",
                "properties": {"issue_id": {"type": "string", "enum": ["issue-101"]}},
                "required": ["issue_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_summary",
            "description": "Read a summary of one local sample file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "enum": ["src/app.py"]},
                    "include_symbols": {"type": "boolean"},
                },
                "required": ["file_id"],
                "additionalProperties": False,
            },
        },
    },
]


def authorize_tool_request(request: ToolRequest) -> ToolAuthorizationDecision:
    """Deterministically enforce known read-only tools, local scope, and parameter contracts."""
    policy = TOOL_POLICIES.get(request.tool_name)
    if policy is None:
        return ToolAuthorizationDecision(False, "Tool identity is not permitted.")
    if request.resource_id not in policy.allowed_resources:
        return ToolAuthorizationDecision(False, "Resource is outside the tool's permitted local scope.")

    for name, value in request.parameters.items():
        validator = policy.parameter_validators.get(name)
        if validator is None or not validator(value):
            return ToolAuthorizationDecision(False, "Tool parameters are not permitted.")
    return ToolAuthorizationDecision(True, "Read-only tool request is permitted.")


def _get_project_info(project_id: str, _: Mapping[str, Any]) -> dict[str, Any]:
    return dict(_PROJECTS[project_id])


def _read_issue(issue_id: str, _: Mapping[str, Any]) -> dict[str, Any]:
    return dict(_ISSUES[issue_id])


def _get_file_summary(file_id: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    summary = dict(_FILES[file_id])
    if not parameters.get("include_symbols", False):
        summary.pop("symbols", None)
    return summary


_READ_ONLY_HANDLERS = {
    "get_project_info": _get_project_info,
    "read_issue": _read_issue,
    "get_file_summary": _get_file_summary,
}


def execute_read_only_tool(request: ToolRequest) -> ToolExecutionResult:
    """Authorize before executing one harmless local lookup; no external or mutating action exists."""
    authorization = authorize_tool_request(request)
    if not authorization.allowed:
        return ToolExecutionResult(False, authorization.reason)

    data = _READ_ONLY_HANDLERS[request.tool_name](request.resource_id, request.parameters)
    return ToolExecutionResult(True, authorization.reason, data)
