# GA4GH MCP Servers

This repository provides a collection of  MCP (Model Context Protocol) servers that enable AI assistants like Claude, Cursor, and Codex to directly execute against GA4GH API endpoints. Each server wraps a specific GA4GH API, providing a standardized interface for AI-driven analysis.


## Purpose

GA4GH-MCP bridges the gap between AI queries and GA4GH standards. While AI excels at designing workflows and interpreting results, GA4GH-MCP handles the technical execution, allowing you to focus on the science rather than the command-line details.

## Available MCP Servers

- **ga4gh-registry** - provides access to the GA4GH Service Registry, allowing you to discover and query GA4GH services including TRS (Tool Registry Service), WES, and other standardized services.

- **ga4gh-trs** - rovides direct access to GA4GH Tool Registry Service (TRS) endpoints, allowing you to discover and query tools, workflows, and their metadata.


## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - fast Python package manager and runner
  ```bash
  # Install uv if you haven't already
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Running the servers

1) Run directly with uv from project root
```bash
# run GA4GH registry server
uv run --directory ga4gh-mcp/servers -- python -m ga4gh_registry.py

# run TRS server
uv run --directory ga4gh-mcp/servers -- python -m ga4gh_trs.py
```


## Testing the server

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

## Claude Desktop / MCP integration

1. Ensure uv is installed on your system
2. Example `claude_desktop_config.json` entry:
```json
"ga4gh-registry": {
  "command": "uv",
  "args": [
    "--directory",
    "ga4gh-mcp/server",
    "run",
    "ga4gh_registry.py"
  ]
},
"ga4gh-trs": {
  "command": "uv",
  "args": [
     "--directory",
    "ga4gh-mcp/server",
    "run",
    "ga4gh_trs.py"
  ]
}

3. Restart Claude Desktop (or use Help → Reload configuration)
4. Servers should now appear in the Tools/Plugins list


## Troubleshooting

- `command not found: uv` - Install uv using the link above
- Module import errors - uv will automatically install dependencies from `pyproject.toml` or `requirements.txt`
- Server exits immediately - Run the same uv command in your terminal to see stderr and diagnose import/runtime errors
- Use `mcp-cli` for easier local testing and interactive calls

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

## License / Links

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

- See GA4GH Service Registry and TRS specs for API details:
  - https://github.com/ga4gh-discovery/ga4gh-service-registry
  - https://github.com/ga4gh/tool-registry-service-schemas

## AI Disclosure

Artificial intelligence tools, including large language models (LLMs), were used during the development of this project to support writing, clarify technical concepts, and assist in generating code snippets. These tools served as an aid for idea refinement, debugging, and improving the readability of explanations and documentation. All AI-generated text and code were thoroughly reviewed, verified for correctness, and understood in full before being incorporated into this work. The responsibility for all final decisions, interpretations, and implementations remains solely with the contributors.