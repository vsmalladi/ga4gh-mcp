from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("ga4gh-registry")

# Constants
GA4GH_REGISTRY_BASE = "https://registry.ga4gh.org/v1"
USER_AGENT = "fairbio-ga4gh/1.0"


async def make_request(url: str, headers: dict | None = None) -> dict[str, Any] | list | None:
    """Make a request to GA4GH APIs with proper error handling."""
    default_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=default_headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_service_type(service_type: Any) -> str:
    """Format a GA4GH service type object or string into a readable string."""
    if isinstance(service_type, dict):
        artifact = service_type.get("artifact", "Unknown")
        version = service_type.get("version", "")
        group = service_type.get("group", "")
        return f"{group}/{artifact}:{version}".strip("/")
    return str(service_type)


def match_service_type(service_type: Any, filter_str: str) -> bool:
    """Check if a service type matches the given filter string.
    
    Matches against the artifact name (e.g. 'trs', 'wes', 'tes', 'drs').
    """
    if isinstance(service_type, dict):
        artifact = service_type.get("artifact", "")
        return artifact.lower() == filter_str.lower()
    return str(service_type).lower() == filter_str.lower()


@mcp.tool()
async def list_services(service_type: str | None = None, registry_url: str | None = None) -> str:
    """List all GA4GH services or filter by type.

    Args:
        service_type: Optional service type filter (trs, wes, tes, drs, etc.)
        registry_url: Optional custom registry URL (defaults to GA4GH official registry)
    """
    base_url = registry_url or GA4GH_REGISTRY_BASE
    url = f"{base_url}/services"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return "Unable to fetch GA4GH services."

    services = data

    if service_type:
        services = [s for s in services if match_service_type(s.get("type"), service_type)]
        if not services:
            return f"No services found with type: {service_type}"

    results = []
    for service in services:
        result = f"""ID: {service.get('id', 'Unknown')}
Type: {format_service_type(service.get('type', 'Unknown'))}
Name: {service.get('name', 'Unknown')}
URL: {service.get('url', 'Unknown')}
Organization: {service.get('organization', {}).get('name', 'Unknown') if isinstance(service.get('organization'), dict) else service.get('organization', 'Unknown')}"""
        results.append(result)

    return f"Found {len(services)} service(s):\n\n" + "\n---\n".join(results)


@mcp.tool()
async def get_service(service_id: str, registry_url: str | None = None) -> str:
    """Get details for a specific GA4GH service.

    Args:
        service_id: Service ID to retrieve
        registry_url: Optional custom registry URL
    """
    base_url = registry_url or GA4GH_REGISTRY_BASE
    url = f"{base_url}/services/{service_id}"
    data = await make_request(url)

    if not data or not isinstance(data, dict):
        return f"Unable to fetch service: {service_id}"

    organization = data.get("organization", {})
    org_name = organization.get("name", "Unknown") if isinstance(organization, dict) else str(organization)

    result = f"""ID: {data.get('id', 'Unknown')}
Type: {format_service_type(data.get('type', 'Unknown'))}
Name: {data.get('name', 'Unknown')}
URL: {data.get('url', 'Unknown')}
Organization: {org_name}
Description: {data.get('description', 'No description')}
Version: {data.get('version', 'Unknown')}
Created: {data.get('created', 'Unknown')}
Updated: {data.get('updated', 'Unknown')}"""

    return result


@mcp.tool()
async def list_service_types(registry_url: str | None = None) -> str:
    """List all available service types in the registry.

    Args:
        registry_url: Optional custom registry URL
    """
    base_url = registry_url or GA4GH_REGISTRY_BASE
    url = f"{base_url}/services"
    data = await make_request(url)

    if not data or not isinstance(data, list):
        return "Unable to fetch services."

    services = data
    type_strings = [format_service_type(s.get("type", "Unknown")) for s in services]
    types = sorted(set(type_strings))

    result = f"Found {len(types)} service type(s):\n"
    for t in types:
        count = sum(1 for s in services if format_service_type(s.get("type", "Unknown")) == t)
        result += f"\n- {t} ({count} service(s))"

    return result


@mcp.tool()
async def get_registry_info(registry_url: str | None = None) -> str:
    """Get information about the GA4GH Service Registry.

    Args:
        registry_url: Optional custom registry URL
    """
    base_url = registry_url or GA4GH_REGISTRY_BASE
    url = f"{base_url}/info"
    data = await make_request(url)

    if not data or not isinstance(data, dict):
        return "Unable to fetch registry information."

    result = f"""Registry Information:
Title: {data.get('title', 'Unknown')}
Version: {data.get('version', 'Unknown')}
Description: {data.get('description', 'No description')}
Total Services: {data.get('service_count', 'Unknown')}
Updated: {data.get('updated', 'Unknown')}"""

    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()