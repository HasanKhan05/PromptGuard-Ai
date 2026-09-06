from app.services.tools import (
    ToolRequest,
    authorize_tool_request,
    execute_read_only_tool,
    _PROJECTS,
    _ISSUES,
    _FILES
)

def test_tool_invariant_admin_core():
    # A. Existence
    assert "admin-core" in _PROJECTS
    req = ToolRequest(tool_name="get_project_info", resource_id="admin-core", parameters={"project_id": "admin-core"})
    
    # B. Policy / Defended Semantics
    decision = authorize_tool_request(req)
    assert decision.allowed is False
    
    # C. Baseline Semantics (Direct mock of execution without policy gate)
    from app.services.tools import _get_project_info
    data = _get_project_info("admin-core", {"project_id": "admin-core"})
    assert data["name"] == "PromptGuard Admin Core"
    
    # D. Defended execution path (gated)
    res = execute_read_only_tool(req)
    assert res.allowed is False

def test_tool_invariant_issue_999():
    assert "issue-999" in _ISSUES
    req = ToolRequest(tool_name="read_issue", resource_id="issue-999", parameters={"issue_id": "issue-999"})
    
    assert authorize_tool_request(req).allowed is False
    
    from app.services.tools import _read_issue
    data = _read_issue("issue-999", {"issue_id": "issue-999"})
    assert data["title"] == "Admin credentials leak"
    
    assert execute_read_only_tool(req).allowed is False

def test_tool_invariant_src_secrets():
    assert "src/secrets.py" in _FILES
    req = ToolRequest(tool_name="get_file_summary", resource_id="src/secrets.py", parameters={"file_id": "src/secrets.py", "include_symbols": True})
    
    assert authorize_tool_request(req).allowed is False
    
    from app.services.tools import _get_file_summary
    data = _get_file_summary("src/secrets.py", {"file_id": "src/secrets.py", "include_symbols": True})
    assert "ADMIN_KEY" in data.get("symbols", [])
    
    assert execute_read_only_tool(req).allowed is False
