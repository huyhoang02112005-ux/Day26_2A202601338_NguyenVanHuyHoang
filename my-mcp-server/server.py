import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from mcp.server.mcpserver import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

# Path to log file
LOG_FILE_PATH = Path(__file__).parent / "data" / "app.log"
SERVER_VERSION = "2.0.0"

# --- Authentication Token Store ---
VALID_TOKENS: Dict[str, str] = {
    os.environ.get("MCP_AUTH_TOKEN", "secret-token-123"): "admin-user",
    "dev-token-abc": "dev-user",
}


class StaticTokenVerifier(TokenVerifier):
    """Xác thực Bearer Token cho Streamable HTTP transport."""

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        client_id = VALID_TOKENS.get(token)
        if client_id is None:
            return None
        return AccessToken(token=token, client_id=client_id, scopes=["logs:read"])


# Initialize MCPServer with Auth capability
mcp = MCPServer(
    "log-analyzer-server",
    instructions=f"Log Analyzer MCP Server v{SERVER_VERSION}. "
    "Hỗ trợ search_logs (v1), search_logs_v2 (v2 JSON), get_error_summary (v1), và get_error_summary_v2 (v2 JSON).",
    auth=AuthSettings(
        issuer_url="http://localhost:8085",
        resource_server_url="http://localhost:8085",
    ),
    token_verifier=StaticTokenVerifier(),
)


# ── Resource: server://info (Bước 6 - Versioning Metadata) ─────────────────────
@mcp.resource("server://info")
def server_info() -> str:
    """Trả về thông tin phiên bản và danh sách các tools khả dụng của Server."""
    return json.dumps(
        {
            "name": "log-analyzer-server",
            "version": SERVER_VERSION,
            "capabilities": {
                "authentication": "Bearer Token",
                "transport": ["stdio", "streamable-http"],
            },
            "tools": {
                "search_logs": {
                    "version": "1.0.0",
                    "deprecated": True,
                    "description": "V1 - Trả về danh sách log định dạng chuỗi đơn giản",
                },
                "search_logs_v2": {
                    "version": "2.0.0",
                    "deprecated": False,
                    "description": "V2 - Trả về cấu trúc JSON chi tiết kèm metadata",
                },
                "get_error_summary": {
                    "version": "1.0.0",
                    "deprecated": True,
                    "description": "V1 - Thống kê cơ bản",
                },
                "get_error_summary_v2": {
                    "version": "2.0.0",
                    "deprecated": False,
                    "description": "V2 - Thống kê JSON nâng cao",
                },
            },
        },
        ensure_ascii=False,
        indent=2,
    )


# ── Tool v1: search_logs (Backward Compatibility) ──────────────────────────────
@mcp.tool()
def search_logs(keyword: str = "", log_level: str = "ALL", limit: int = 20) -> List[str]:
    """[v1 - Legacy] Tìm kiếm các dòng log theo từ khóa và level (trả về chuỗi đơn giản).

    Args:
        keyword: Từ khóa cần tìm (vd: 'timeout', 'database', 'payment')
        log_level: Mức độ log cần lọc ('INFO', 'WARNING', 'ERROR', 'CRITICAL', hoặc 'ALL')
        limit: Số lượng dòng log tối đa cần trả về (mặc định: 20)
    """
    if not LOG_FILE_PATH.exists():
        return [f"Error: Log file not found at {LOG_FILE_PATH}"]

    matched_logs = []
    log_level_upper = log_level.upper()
    keyword_lower = keyword.lower()

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            if log_level_upper != "ALL" and f"[{log_level_upper}]" not in line_str:
                continue

            if keyword_lower and keyword_lower not in line_str.lower():
                continue

            matched_logs.append(line_str)
            if len(matched_logs) >= limit:
                break

    return matched_logs


# ── Tool v2: search_logs_v2 (Mới, JSON format + Metadata + Optional Params) ──────
@mcp.tool()
def search_logs_v2(
    keyword: str = "",
    log_level: str = "ALL",
    limit: int = 20,
    case_sensitive: bool = False,
    include_line_numbers: bool = True,
) -> str:
    """[v2 - Recommended] Tìm kiếm log nâng cao — Trả về định dạng JSON chi tiết.

    Args:
        keyword: Từ khóa tìm kiếm
        log_level: Mức độ log ('INFO', 'WARNING', 'ERROR', 'CRITICAL', hoặc 'ALL')
        limit: Giới hạn số kết quả trả về
        case_sensitive: Phân biệt chữ hoa/chữ thường (Mặc định: False)
        include_line_numbers: Kèm chỉ số dòng log trong file (Mặc định: True)
    """
    if not LOG_FILE_PATH.exists():
        return json.dumps({"error": f"Log file not found at {LOG_FILE_PATH}"}, ensure_ascii=False)

    results = []
    log_level_upper = log_level.upper()

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue

            if log_level_upper != "ALL" and f"[{log_level_upper}]" not in line_str:
                continue

            matched = (
                (keyword in line_str)
                if case_sensitive
                else (keyword.lower() in line_str.lower())
            )
            if not matched and keyword:
                continue

            # Parse log entry format: YYYY-MM-DD HH:MM:SS [LEVEL] Message
            parts = line_str.split(" ", 3)
            log_item = {
                "raw": line_str,
                "timestamp": f"{parts[0]} {parts[1]}" if len(parts) >= 2 else "",
                "level": parts[2].strip("[]") if len(parts) >= 3 else "UNKNOWN",
                "message": parts[3] if len(parts) >= 4 else line_str,
            }
            if include_line_numbers:
                log_item["line_number"] = line_idx

            results.append(log_item)
            if len(results) >= limit:
                break

    output = {
        "api_version": "2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": {
            "keyword": keyword,
            "log_level": log_level,
            "limit": limit,
            "case_sensitive": case_sensitive,
        },
        "total_matched": len(results),
        "results": results,
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


# ── Tool v1: get_error_summary (Backward Compatibility) ────────────────────────
@mcp.tool()
def get_error_summary() -> Dict[str, Any]:
    """[v1 - Legacy] Thống kê lỗi cơ bản (trả về dictionary cũ)."""
    if not LOG_FILE_PATH.exists():
        return {"error": f"Log file not found at {LOG_FILE_PATH}"}

    summary = {
        "total_lines": 0,
        "counts": {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
        "recent_errors": [],
    }

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            summary["total_lines"] += 1

            for level in summary["counts"].keys():
                if f"[{level}]" in line_str:
                    summary["counts"][level] += 1
                    if level in ("ERROR", "CRITICAL"):
                        summary["recent_errors"].append(line_str)
                    break

    summary["recent_errors"] = summary["recent_errors"][-5:]
    return summary


# ── Tool v2: get_error_summary_v2 (Mới, JSON format nâng cao) ──────────────────
@mcp.tool()
def get_error_summary_v2(top_n_errors: int = 5) -> str:
    """[v2 - Recommended] Thống kê tổng quan log & phân tích lỗi chi tiết dạng JSON.

    Args:
        top_n_errors: Số lượng lỗi mới nhất cần trích xuất (Mặc định: 5)
    """
    if not LOG_FILE_PATH.exists():
        return json.dumps({"error": f"Log file not found at {LOG_FILE_PATH}"}, ensure_ascii=False)

    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
    recent_errors = []
    total_lines = 0

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            total_lines += 1

            for level in counts.keys():
                if f"[{level}]" in line_str:
                    counts[level] += 1
                    if level in ("ERROR", "CRITICAL"):
                        recent_errors.append(line_str)
                    break

    output = {
        "api_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_log_entries": total_lines,
        "level_breakdown": counts,
        "error_rate_percentage": round(
            (counts["ERROR"] + counts["CRITICAL"]) / (total_lines or 1) * 100, 2
        ),
        "recent_critical_and_errors": recent_errors[-top_n_errors:],
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    transport = os.getenv("TRANSPORT", "stdio").lower()
    port = int(os.getenv("PORT", 8085))

    if transport == "streamable-http":
        print(f"🚀 Starting Log Analyzer MCP Server (v{SERVER_VERSION}) on http://0.0.0.0:{port}/mcp [Streamable HTTP]")
        print(f"🔑 Valid Bearer Tokens: 'secret-token-123', 'dev-token-abc'")
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        print(f"🚀 Running Log Analyzer MCP Server (v{SERVER_VERSION}) in STDIO mode...")
        mcp.run()
