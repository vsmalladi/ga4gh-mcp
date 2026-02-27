# GA4GH MCP Servers

This repository provides example MCP (Model Context Protocol) servers for GA4GH endpoints.

Quick contents
- ga4gh_registry (GA4GH Service Registry) — run the module that exposes tools to list/query services
- ga4gh_trs (TRS) — run the TRS server that exposes tools to list/query tools, versions, descriptors

Prerequisites
- Python 3.10+
- Install runtime deps in the interpreter that will run the servers:
  pip install httpx mcp

Start servers (examples)

1) Run directly with Python (project dir = this repo)
```bash
# run GA4GH registry server (if you have ga4gh_registry.py)
python -m ga4gh_registry

# run TRS server
python -m ga4gh_trs

# alternatively run files directly
python ga4gh_trs.py
```

2) Use uv (if you use uv/env tooling)
```bash
# run from repo root using uv, forwarding a python -m command
uv --directory /Users/Venkat/OpenSource/GA4GH/ga4gh-mcp run -- python -m ga4gh_trs
```

3) Use mcp-cli to run servers from a toml config
```toml
# example mcp.toml
[trs]
command = "python"
args = ["-m", "ga4gh_trs"]

[ga4gh-registry]
command = "python"
args = ["-m", "ga4gh_registry"]
```

Run:
```bash
mcp run -c /path/to/mcp.toml
```

Testing the server

- List available tools:
Send this JSON-RPC to the running process (method `tools/list`):
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

- Call a tool (method `tools/call`):
```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_tools","args":{"registry_url":"https://dockstore.org/api/ga4gh/trs/v2"}}}
```

Quick `echo | python` test
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_tools","args":{"registry_url":"https://dockstore.org/api/ga4gh/trs/v2"}}}' \
  | python -m ga4gh_trs
```

Claude Desktop / MCP integration
- Ensure the process Claude spawns can import the module and has deps installed.
- Example claude_desktop_config.json entry (use full uv or python path to match your environment):
```json
"trs": {
  "command": "uv",
    "args": [
        "--directory",
        "gagh-mcp",
        "run",
        "ga4gh_registry.py"
    ]
}
```

Troubleshooting
- ModuleNotFoundError: install missing packages in the interpreter Claude/uv uses (pip install httpx mcp).
- If the server exits immediately, run the same command in a terminal to see stderr and fix import errors.
- Use `mcp-cli` for easier local testing and interactive calls.


## Example queries (convenience tools)

The GA4GH registry server exposes convenience tools for common queries. Use mcp-cli or JSON‑RPC to call them.

- Give me a list of all services in the GA4GH registry
  - mcp-cli:
    ```bash
    mcp call list_all_services -s ga4gh-registry -c /Users/Venkat/OpenSource/GA4GH/ga4gh-mcp/mcp.toml
    ```
  - JSON-RPC:
    ```json
    {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_all_services","args":{}}}
    ```

- Give me all the information on the Dockstore TRS service
  - mcp-cli:
    ```bash
    mcp call dockstore_trs_info -s ga4gh-registry -c /Users/Venkat/OpenSource/GA4GH/ga4gh-mcp/mcp.toml
    ```
  - JSON-RPC:
    ```json
    {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"dockstore_trs_info","args":{}}}
    ```

- Give me a summary of samtools versions from Dockstore
  - mcp-cli:
    ```bash
    mcp call summarize_samtools_versions_from_dockstore -s ga4gh-registry -c /Users/Venkat/OpenSource/GA4GH/ga4gh-mcp/mcp.toml
    ```
  - JSON-RPC:
    ```json
    {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"summarize_samtools_versions_from_dockstore","args":{}}}
    ```

Note: Ensure the ga4gh-registry server is running and accessible to mcp or Claude Desktop. These tools are implemented in `ga4gh_registry.py`.

License / Links
- See GA4GH Service Registry and TRS specs for API details:
  - https://github.com/ga4gh-discovery/ga4gh-service-registry
  - https://github.com/ga4gh/tool-registry-service-schemas