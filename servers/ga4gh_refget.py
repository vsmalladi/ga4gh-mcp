from mcp.server.fastmcp import FastMCP
import httpx
import hashlib
import base64
import re
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("refget")

# Constants
USER_AGENT = "fairbio-refget/1.0"
# Timeout in seconds
TIMEOUT = 30
CLIENT = httpx.AsyncClient(timeout=TIMEOUT)


@mcp.tool()
async def refget_collections(url: str, limit: int = 5) -> dict:
    """
    List sequence collections from refget server.
    
    Args:
        url: Base URL of the refget server (e.g., https://seqcolapi.databio.org)
        limit: Maximum number of results to return
    
    Returns:
        List of matching collections
    """
    try:
        r = await CLIENT.get(
            f"{url}/list/collections",
            params={"limit": limit},
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
        return {
            "status": "success",
            "count": len(data.get("collections", [])),
            "collections": data.get("collections", [])
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "url": f"{url}/list/collections"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_get_collection(url: str, digest: str, level: Optional[int] = None, collated: Optional[bool] = None, attribute: Optional[str] = None) -> dict:
    """
    Fetch a sequence collection by digest.
    
    Args:
        url: Base URL of the refget server (e.g., https://seqcolapi.databio.org)
        digest: Collection digest (e.g., "sha256:abc123...")
        level: Recursion depth (1 or 2, optional)
        collated: Return collated format (default true, optional)
        attribute: Return only this attribute (e.g., 'names', 'lengths', optional)
    
    Returns:
        Collection metadata and sequence information
    """
    try:
        params = {}
        if level is not None:
            params["level"] = level
        if collated is not None:
            params["collated"] = collated
        if attribute is not None:
            params["attribute"] = attribute
        
        r = await CLIENT.get(
            f"{url}/collection/{digest}",
            params=params,
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": "Collection not found",
                "digest": digest
            }
        
        r.raise_for_status()
        return {
            "status": "success",
            "digest": digest,
            "collection": r.json()
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "digest": digest
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
