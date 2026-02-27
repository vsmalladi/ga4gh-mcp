from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("trs")

# Constants
USER_AGENT = "fairbio-trs/1.0"


async def make_request(url: str, params: dict | None = None) -> Any | None:
    """Make a request to TRS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.tool()
async def list_tools(registry_url: str, limit: int = 1000, offset: int = 0, all_tools: bool = False) -> str:
    """List tools in a TRS registry.

    Args:
        registry_url: TRS registry URL (e.g., https://dockstore.org/api/ga4gh/trs/v2)
        limit: Page size for results (default: 1000)
        offset: Start index for pagination
        all_tools: Whether to fetch all tools by auto-paginating
    """
    url = f"{registry_url}/tools"
    params = {"limit": limit, "offset": offset}

    # TRS returns a plain list of tools
    data = await make_request(url, params)

    if not data or not isinstance(data, list):
        return "Unable to fetch tools from TRS registry."

    tools = data

    results = []
    for tool in tools[:20]:  # Show first 20
        result = f"""ID: {tool.get('id', 'Unknown')}
Name: {tool.get('name', 'Unknown')}
Organization: {tool.get('organization', 'Unknown')}
Description: {tool.get('description', 'No description')}
Versions: {len(tool.get('versions', []))}"""
        results.append(result)

    summary = f"Found {len(tools)} tool(s)"
    if len(tools) == limit:
        summary += f" (showing first {len(tools)}, use offset for pagination)"

    return summary + ":\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_tool(registry_url: str, tool_id: str) -> str:
    """Get details for a specific tool.

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID to retrieve
    """
    url = f"{registry_url}/tools/{tool_id}"
    data = await make_request(url)

    if not data:
        return f"Unable to fetch tool: {tool_id}"

    result = f"""ID: {data.get('id', 'Unknown')}
Name: {data.get('name', 'Unknown')}
Organization: {data.get('organization', 'Unknown')}
Author: {data.get('author', 'Unknown')}
Description: {data.get('description', 'No description')}
URL: {data.get('url', 'Unknown')}
Total Versions: {len(data.get('versions', []))}"""

    return result


@mcp.tool()
async def list_tool_versions(registry_url: str, tool_id: str) -> str:
    """List all versions of a tool.

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
    """
    url = f"{registry_url}/tools/{tool_id}/versions"

    # TRS returns a plain list of versions
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return f"Unable to fetch versions for tool: {tool_id}"

    versions = data

    results = []
    for version in versions:
        result = f"""Version: {version.get('id', 'Unknown')}
Name: {version.get('name', 'Unknown')}
Created: {version.get('meta_version', 'Unknown')}
Descriptor Types: {', '.join(version.get('descriptor_type', []))}
Verified: {version.get('verified', False)}"""
        results.append(result)

    return f"Found {len(versions)} version(s):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_tool_descriptor(registry_url: str, tool_id: str, version: str, descriptor_type: str) -> str:
    """Get tool descriptor (CWL, WDL, etc.).

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
        descriptor_type: Descriptor type (CWL, WDL, NFL, GALAXY, SMK, etc.)
    """
    # Correct TRS v2 descriptor endpoint
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/{descriptor_type.upper()}/descriptor"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            # TRS returns a FileWrapper with a 'content' field
            return data.get("content", response.text)
        except Exception:
            return f"Unable to fetch {descriptor_type} descriptor for tool {tool_id} version {version}"


@mcp.tool()
async def list_tool_classes(registry_url: str) -> str:
    """List all tool classes available in the TRS.

    Args:
        registry_url: TRS registry URL
    """
    url = f"{registry_url}/toolClasses"

    # TRS returns a plain list of tool classes
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return "Unable to fetch tool classes."

    classes = data

    results = []
    for tool_class in classes:
        result = f"""ID: {tool_class.get('id', 'Unknown')}
Name: {tool_class.get('name', 'Unknown')}
Description: {tool_class.get('description', 'No description')}"""
        results.append(result)

    return f"Found {len(classes)} tool class(es):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_trs_info(registry_url: str) -> str:
    """Get TRS service information.

    Args:
        registry_url: TRS registry URL
    """
    # Correct TRS endpoint is /service-info, not /metadata
    url = f"{registry_url}/service-info"
    data = await make_request(url)

    if not data:
        return "Unable to fetch TRS service info."

    org = data.get("organization", {})
    result = f"""TRS Service Information:
Name: {data.get('name', 'Unknown')}
Version: {data.get('version', 'Unknown')}
API Version: {data.get('type', {}).get('version', 'Unknown')}
Description: {data.get('description', 'Unknown')}
Organization: {org.get('name', 'Unknown')}
Organization URL: {org.get('url', 'Unknown')}
Contact URL: {data.get('contactUrl', 'Unknown')}
Documentation URL: {data.get('documentationUrl', 'Unknown')}"""

    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()