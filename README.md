# GA4GH MCP Servers

A collection of Model Context Protocol (MCP) servers for GA4GH (Global Alliance for Genomics and Health) genomic data standards and tools. These servers enable AI agents and applications to discover, query, and access genomic reference data through a standardized interface.

## Purpose

GA4GH-MCP bridges the gap between AI queries and GA4GH standards. While AI excels at designing workflows and interpreting results, GA4GH-MCP handles the technical execution, allowing you to focus on the science rather than the command-line details.

## Available MCP Servers

- **ga4gh-registry** - Provides access to the GA4GH Service Registry, allowing you to discover and query GA4GH services including TRS (Tool Registry Service), WES, and other standardized services.

- **ga4gh-trs** - Provides direct access to GA4GH Tool Registry Service (TRS) endpoints, allowing you to discover and query tools, workflows, and their metadata.

- **ga4gh-refget** - Retrieve and validate biological sequences and collections via GA4GH refget APIs. Supports digest computation, sequence and collection lookup, and FASTA ingestion.

- **refgenie** - Discover and access reference genome assets, annotations, and download paths from a refgenie server.


## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - fast Python package manager and runner
  ```bash
  # Install uv if you haven't already
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Setup

1. Create and activate a virtual environment
```bash
   uv venv
   source .venv/bin/activate
```

2. Install dependencies
```bash
   uv add "mcp[cli]" httpx
```

3. Install nvm if you don't have it
```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal then install and use Node 20
nvm install 20
nvm use 20
```

## Running the servers

1) Run directly with uv from project root
```bash
# run GA4GH registry server
uv run --directory servers -- python -m ga4gh_registry

# run TRS server
uv run --directory servers -- python -m ga4gh_trs.py

# run Refget server
uv run --directory servers -- python -m ga4gh_refget.py

# run Refgenie server
uv run --directory servers -- python -m refgenie.py

```


## Testing the server

The easiest way to test and debug the servers is with the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) — an interactive tool that runs directly via `npx` with no installation required.

Launch the inspector against a locally installed server:
```bash
# GA4GH Registry server
npx @modelcontextprotocol/inspector uv --directory . run ga4gh_registry.py

# TRS server
npx @modelcontextprotocol/inspector uv --directory . run ga4gh_trs.py

# Refget server
npx @modelcontextprotocol/inspector uv --directory . run ga4gh_refget.py

# Refgenie server
npx @modelcontextprotocol/inspector uv --directory . run refgenie.py
```

Once running, the Inspector opens a browser UI where you can:

- **Tools tab** — browse available tools, view their schemas, and invoke them with custom inputs
- **Resources tab** — inspect any exposed resources and their metadata
- **Notifications pane** — view logs and server-emitted notifications in real time

This is the recommended approach for iterative development: make a change, restart the server, reconnect the Inspector, and test the affected tools.

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
},
"ga4gh-refget": {
  "command": "uv",
  "args": [
     "--directory",
    "ga4gh-mcp/server",
    "run",
    "ga4gh_refget.py"
  ]
},
"refgenie": {
  "command": "uv",
  "args": [
     "--directory",
    "ga4gh-mcp/server",
    "run",
    "refgenie.py"
  ]
},
```

3. Restart Claude Desktop (or use Help → Reload configuration)
4. Servers should now appear in the Tools/Plugins list


## Troubleshooting

- `command not found: uv` - Install uv using the link above
- Module import errors - uv will automatically install dependencies from `pyproject.toml` or `requirements.txt`
- Server exits immediately - Run the same uv command in your terminal to see stderr and diagnose import/runtime errors
- Use `mcp-cli` or `MCP Inspector` for easier local testing and interactive calls

## Example queries (convenience tools)

The GA4GH registry server exposes convenience tools for common queries. 

```
User: "Give me a list of all services in the GA4GH registry"
AI: [calls ga4gh-registry] -> Returns summary table of GA4GH servies registered
```

```
User: "Give me all the information on the Dockstore TRS service"
AI: [calls ga4gh-registry] -> Returns Dockstore Service info -> [calls ga4gh-trs] -> Returns TRS service Info -> Summary table of From GA$GH registry and live TRS endpoint
```


```
User: "Give me a summary of samtools versions from Biocontainers"
AI: [calls ga4gh-trs] -> Returns Bioconstainers list of all avaiable Samtools versions and hilighting the latest version as well as duplicate/conflicting version numbers.
```

```
User: "Get me a list of RNAseq workflows from dockstore and group by language"
AI: [calls ga4gh-trs] -> Search using terms RNA-seq and aliases -> Returns table of workflows matching search pattern broken up by workflow language and given number of versions for each
```


```
User: "Find Human Reference Sequence from https://api.refgenie.org/"
AI: [calls refgenie] -> Search for all Human assets using aliases -> Returns a list of human references assets by id that match aliases 
```


## Available Tools

### ga4gh-registry

Provides access to the GA4GH Service Registry for discovering and querying registered GA4GH services.

| Tool | Description |
|---|---|
| `list_services` | List all services, optionally filtered by type (`trs`, `wes`, `tes`, `drs`, etc.) |
| `get_service` | Get full details for a specific service by ID |
| `list_service_types` | List all distinct service types present in the registry |
| `get_registry_info` | Get metadata about the registry itself |

All tools accept an optional `registry_url` parameter to target a custom registry (defaults to `https://registry.ga4gh.org/v1`).

### ga4gh-trs

Provides direct access to any GA4GH Tool Registry Service (TRS) endpoint for discovering tools, workflows, and their metadata.

| Tool | Description |
|---|---|
| `get_trs_info` | Get service metadata for a TRS instance |
| `list_tools` | List tools in a TRS registry, with pagination support |
| `get_tool` | Get details for a specific tool by ID |
| `list_tool_versions` | List all versions of a tool |
| `get_tool_descriptor` | Fetch a tool descriptor (CWL, WDL, NFL, GALAXY, SMK, etc.) for a specific version |
| `list_tool_classes` | List all tool classes available in the TRS |

All tools require a `registry_url` argument (e.g. `https://dockstore.org/api/ga4gh/trs/v2` or `https://api.biocontainers.pro/ga4gh/trs/v2`).

### ga4gh-refget

Provides direct access to any GA4GH Refget endpoint discovering genomes.

| Tool                     | Description                      |
| ------------------------ | -------------------------------- |
| `refget_search`          | Search collections               |
| `refget_get_collection`  | Fetch collection metadata        |
| `refget_get_sequence`    | Retrieve sequence by digest      |
| `refget_upload_fasta`    | Upload FASTA and compute digests |
| `refget_verify_sequence` | Validate sequence vs digest      |


### refgenie

Discover and access reference genome assets, aliases, and remote download paths from a refgenie server.

| Tool | Description |
|---|---|
| `refgenie_set_url` | Configure or override the refgenie server URL for subsequent requests |
| `refgenie_get_url` | Check the current refgenie server URL, connection status, and server info |
| `refgenie_list_genomes` | List all available genome digests from the configured refgenie instance |
| `refgenie_get_genome` | Find genomes by alias using fuzzy matching across known genome identifiers |
| `refgenie_get_genome_digest` | Resolve a genome alias to its canonical genome digest |
| `refgenie_list_assets` | List available assets for a genome digest, optionally including seek keys |
| `refgenie_search_assets` | Search for genomes that carry a specific asset type |
| `refgenie_get_asset_path` | Retrieve the asset access path or download URL, including remoteClass support for HTTP/S3 |


## License / Links

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

- See GA4GH Specs:
  - https://github.com/ga4gh-discovery/ga4gh-service-registry
  - https://github.com/ga4gh/tool-registry-service-schemas
  - https://github.com/ga4gh/refget

- Other Specs
  - Refgenie: https://refgenie.databio.org

## AI Disclosure

Artificial intelligence tools, including large language models (LLMs), were used during the development of this project to support writing, clarify technical concepts, and assist in generating code snippets. These tools served as an aid for idea refinement, debugging, and improving the readability of explanations and documentation. All AI-generated text and code were thoroughly reviewed, verified for correctness, and understood in full before being incorporated into this work. The responsibility for all final decisions, interpretations, and implementations remains solely with the contributors.