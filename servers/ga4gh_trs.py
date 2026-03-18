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

    if all_tools:
        all_tool_list = []
        current_offset = offset
        while True:
            params = {"limit": limit, "offset": current_offset}
            data = await make_request(url, params)
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            all_tool_list.extend(data)
            if len(data) < limit:
                break
            current_offset += limit

        tools = all_tool_list
        summary = f"Found {len(tools)} tool(s) (all pages fetched)"
    else:
        params = {"limit": limit, "offset": offset}
        data = await make_request(url, params)
        if not data or not isinstance(data, list):
            return "Unable to fetch tools from TRS registry."
        tools = data
        summary = f"Found {len(tools)} tool(s)"
        if len(tools) == limit:
            summary += f" (page of {limit}, use offset for next page)"

    results = []
    for tool in tools[:20]:  # Show first 20
        result = f"""ID: {tool.get('id', 'Unknown')}
Name: {tool.get('name', 'Unknown')}
Organization: {tool.get('organization', 'Unknown')}
Description: {tool.get('description', 'No description')}
Versions: {len(tool.get('versions', []))}"""
        results.append(result)

    if len(tools) > 20:
        results.append(f"... and {len(tools) - 20} more")

    return summary + ":\n\n" + "\n---\n".join(results)


@mcp.tool()
async def search_tools(
    registry_url: str,
    query: str | None = None,
    descriptor_type: str | None = None,
    author: str | None = None,
    limit: int = 1000,
) -> str:
    """Search for tools using common filters (convenience wrapper around list_tools).

    Args:
        registry_url: TRS registry URL (e.g., https://dockstore.org/api/ga4gh/trs/v2)
        query: Search term matched against tool name / toolname
        descriptor_type: Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)
        author: Filter by tool author
        limit: Maximum number of results (default: 1000)
    """
    url = f"{registry_url}/tools"
    params: dict = {"limit": limit}
    if query:
        params["name"] = query
    if descriptor_type:
        params["descriptorType"] = descriptor_type
    if author:
        params["author"] = author

    data = await make_request(url, params)

    if not data or not isinstance(data, list):
        return "Unable to search tools from TRS registry."

    tools = data
    results = []
    for tool in tools[:20]:
        result = f"""ID: {tool.get('id', 'Unknown')}
Name: {tool.get('name', 'Unknown')}
Organization: {tool.get('organization', 'Unknown')}
Author: {tool.get('author', 'Unknown')}
Description: {tool.get('description', 'No description')}
Versions: {len(tool.get('versions', []))}"""
        results.append(result)

    if len(tools) > 20:
        results.append(f"... and {len(tools) - 20} more")

    summary = f"Found {len(tools)} tool(s)"
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
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return f"Unable to fetch versions for tool: {tool_id}"

    versions = data
    results = []
    for version in versions:
        result = f"""Version: {version.get('id', 'Unknown')}
Name: {version.get('name', 'Unknown')}
Meta Version: {version.get('meta_version', 'Unknown')}
Descriptor Types: {', '.join(version.get('descriptor_type', []))}
Is Production: {version.get('is_production', False)}
Verified: {version.get('verified', False)}"""
        results.append(result)

    return f"Found {len(versions)} version(s):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_tool_version(registry_url: str, tool_id: str, version_id: str) -> str:
    """Get details for a specific version of a tool.

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version_id: Version identifier (e.g., 'v1.0.0')
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version_id}"
    data = await make_request(url)

    if not data:
        return f"Unable to fetch version '{version_id}' for tool: {tool_id}"

    images = data.get('images', [])
    image_names = ', '.join(img.get('image_name', '') for img in images[:5]) if images else 'None'
    if len(images) > 5:
        image_names += f" ... and {len(images) - 5} more"

    result = f"""ID: {data.get('id', 'Unknown')}
Name: {data.get('name', 'Unknown')}
URL: {data.get('url', 'Unknown')}
Meta Version: {data.get('meta_version', 'Unknown')}
Descriptor Types: {', '.join(data.get('descriptor_type', []))}
Is Production: {data.get('is_production', False)}
Verified: {data.get('verified', False)}
Container Images: {image_names}"""

    return result


@mcp.tool()
async def get_tool_descriptor(registry_url: str, tool_id: str, version: str, descriptor_type: str) -> str:
    """Get the primary tool descriptor (CWL, WDL, etc.).

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
        descriptor_type: Descriptor type (CWL, WDL, NFL, GALAXY, SMK, PLAIN_CWL, PLAIN_WDL, etc.)
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/{descriptor_type.upper()}/descriptor"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("content", response.text)
        except Exception:
            return f"Unable to fetch {descriptor_type} descriptor for tool {tool_id} version {version}"


@mcp.tool()
async def get_tool_descriptor_by_path(
    registry_url: str,
    tool_id: str,
    version: str,
    descriptor_type: str,
    relative_path: str,
) -> str:
    """Get a secondary/additional descriptor file by relative path.

    Maps to GET /tools/{id}/versions/{version_id}/{type}/descriptor/{relative_path}

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
        descriptor_type: Descriptor type (CWL, WDL, NFL, GALAXY, SMK, etc.)
        relative_path: Relative path to the secondary descriptor file (e.g., 'tools/helper.cwl')
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/{descriptor_type.upper()}/descriptor/{relative_path}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("content", response.text)
        except Exception:
            return (
                f"Unable to fetch {descriptor_type} descriptor at path '{relative_path}' "
                f"for tool {tool_id} version {version}"
            )


@mcp.tool()
async def get_tool_files(
    registry_url: str,
    tool_id: str,
    version: str,
    descriptor_type: str,
) -> str:
    """Get a list of all files for a tool version.

    Maps to GET /tools/{id}/versions/{version_id}/{type}/files

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
        descriptor_type: Descriptor type (CWL, WDL, NFL, GALAXY, SMK, etc.)
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/{descriptor_type.upper()}/files"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return f"Unable to fetch files for tool {tool_id} version {version} ({descriptor_type})."

    results = []
    for f in data:
        results.append(f"Path: {f.get('path', 'Unknown')}  |  Type: {f.get('file_type', 'Unknown')}")

    return f"Found {len(data)} file(s):\n\n" + "\n".join(results)


@mcp.tool()
async def get_tool_tests(
    registry_url: str,
    tool_id: str,
    version: str,
    descriptor_type: str,
) -> str:
    """Get test parameter files for a specific tool version.

    Maps to GET /tools/{id}/versions/{version_id}/{type}/tests

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
        descriptor_type: Descriptor type (CWL, WDL, NFL, GALAXY, SMK, etc.)
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/{descriptor_type.upper()}/tests"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return f"Unable to fetch test files for tool {tool_id} version {version} ({descriptor_type})."

    results = []
    for test in data:
        content_preview = (test.get('content') or '')[:300]
        entry = f"URL: {test.get('url', 'Unknown')}"
        if content_preview:
            entry += f"\nContent preview:\n{content_preview}"
            if len(test.get('content', '')) > 300:
                entry += "\n... (truncated)"
        results.append(entry)

    return f"Found {len(data)} test file(s):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_tool_containerfile(registry_url: str, tool_id: str, version: str) -> str:
    """Get container specification(s) for a tool version (Dockerfiles, Singularity recipes, etc.).

    Maps to GET /tools/{id}/versions/{version_id}/containerfile

    Args:
        registry_url: TRS registry URL
        tool_id: Tool ID
        version: Version ID
    """
    url = f"{registry_url}/tools/{tool_id}/versions/{version}/containerfile"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return f"Unable to fetch containerfile(s) for tool {tool_id} version {version}."

    results = []
    for cf in data:
        content_preview = (cf.get('content') or '')[:500]
        entry = f"URL: {cf.get('url', 'Unknown')}"
        if content_preview:
            entry += f"\nContent preview:\n{content_preview}"
            if len(cf.get('content', '')) > 500:
                entry += "\n... (truncated)"
        results.append(entry)

    return f"Found {len(data)} containerfile(s):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def list_tool_classes(registry_url: str) -> str:
    """List all tool classes available in the TRS.

    Args:
        registry_url: TRS registry URL
    """
    url = f"{registry_url}/toolClasses"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return "Unable to fetch tool classes."

    results = []
    for tool_class in data:
        result = f"""ID: {tool_class.get('id', 'Unknown')}
Name: {tool_class.get('name', 'Unknown')}
Description: {tool_class.get('description', 'No description')}"""
        results.append(result)

    return f"Found {len(data)} tool class(es):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_trs_info(registry_url: str) -> str:
    """Get TRS service information.

    Args:
        registry_url: TRS registry URL
    """
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