from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import difflib

# Initialize FastMCP server
mcp = FastMCP("refgenie")

# Constants
USER_AGENT = "refgenie-mcp/1.0"
# Get base URL from environment variable or use default
BASE_URL = os.getenv("REFGENIE_URL", "http://refgenomes.databio.org")
# Timeout in seconds
TIMEOUT = int(os.getenv("REFGENIE_TIMEOUT", "30"))
CLIENT = httpx.AsyncClient(timeout=TIMEOUT)


@mcp.tool()
async def refgenie_set_url(url: str) -> dict:
    """
    Set the refgenie server URL for subsequent requests.
    
    Args:
        url: Base URL of the refgenie server (e.g., http://refgenomes.databio.org)
    
    Returns:
        Confirmation message with the set URL
    """
    global BASE_URL
    BASE_URL = url.rstrip("/")  # Remove trailing slash if present
    return {
        "status": "success",
        "message": f"Refgenie URL set to: {BASE_URL}",
        "url": BASE_URL,
    }


@mcp.tool()
async def refgenie_get_url() -> dict:
    """
    Get the current refgenie server URL and configuration.
    
    Returns:
        Current URL, and server information
    """
    try:
        # Try to get server info
        r = await CLIENT.get(
            f"{BASE_URL}/api/serverinfo",
            headers={"User-Agent": USER_AGENT}
        )
        if r.status_code == 200:
            server_info = r.json()
        else:
            server_info = None
    except Exception:
        server_info = None
    
    return {
        "url": BASE_URL,
        "user_agent": USER_AGENT,
        "timeout": TIMEOUT,
        "server_info": server_info
    }


@mcp.tool()
async def refgenie_list_genomes() -> dict:
    """
    List all available genomes digests on the refgenie server.
    
    Returns:
        List of available genomes digests
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/genomes/list",
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
        
        genomes = data.get("genomes", []) if isinstance(data, dict) else data
        
        return {
            "status": "success",
            "count": len(genomes),
            "genomes": genomes
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_genome(genome_alias: str) -> dict:
    """
    Get genome digests with aliases similar to the given genome alias.
    
    Args:
        genome_alias: Genome identifier or alias (e.g., "hg38", "mm10", "human_repeats")
    
    Returns:
        Genome digests and associated aliases that are similar to the input alias
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/genomes/alias_dict",
            headers={"User-Agent": USER_AGENT}
        )
        
        r.raise_for_status()
        try:
            alias_dict = r.json()
        except ValueError:
            # Response is not valid JSON
            return {
                "status": "error",
                "error": f"Invalid JSON response from server",
                "genome_alias": genome_alias
            }
        
        # Ensure alias_dict is a dictionary
        if not isinstance(alias_dict, dict):
            return {
                "status": "error",
                "error": f"Expected dictionary response, got {type(alias_dict).__name__}",
                "genome_alias": genome_alias
            }
        
        # Find similar aliases using fuzzy matching
        matches = []
        genome_alias_lower = genome_alias.lower()
        
        for digest, aliases in alias_dict.items():
            if not isinstance(aliases, list):
                continue
            for alias in aliases:
                # Calculate similarity ratio
                ratio = difflib.SequenceMatcher(None, genome_alias_lower, alias.lower()).ratio()
                if ratio > 0.6:  # Similarity threshold
                    matches.append({
                        "digest": digest,
                        "alias": alias,
                        "aliases": aliases,
                        "similarity": round(ratio, 3)
                    })

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return top matches
        if matches:
            return {
                "status": "success",
                "genome_alias": genome_alias,
                "count": len(matches),
                "matches": matches[:10]  # Return top 10 matches
            }
        else:
            # If no similar matches, return some examples
            return {
                "status": "error",
                "error": f"No similar genome aliases found for: {genome_alias}",
                "available_aliases": list(alias_dict.keys())[:10]  # Show first 10 digests
            }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "genome_alias": genome_alias
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_genome_digest(genome_alias: str) -> dict:
    """
    Get the digest for a genome by its alias.
    
    Args:
        genome_alias: Genome identifier or alias (e.g., "hg38", "mm10")
    
    Returns:
        Digest for the genome
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/genomes/genome_digest/{genome_alias}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Genome not found: {genome_alias}"
            }
        
        r.raise_for_status()
        try:
            data = r.json()
            digest_value = data.get("digest") if isinstance(data, dict) else data
        except ValueError:
            # Response is plain text (just the digest), not JSON
            digest_value = r.text.strip()
        
        return {
            "status": "success",
            "genome_alias": genome_alias,
            "digest": digest_value,
            "timestamp": datetime.now().isoformat()
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_list_assets(genome_digest: Optional[str] = None, seek_key: bool = False) -> dict:
    """
    List all available assets for a specific genome.
    
    Args:
        genome_digest: Optional Genome digest (e.g., "8baf9d24ad8f5678f0fe1f5b21a812d410755d49e3123158") filter
        seek_key: Whether to include the seek key in the response
    
    Returns:
        List of available assets for digests matching the filter or all genomes if no filter is provided
    """
    try:
        if seek_key:
            # Get seek key if requested
            r = await CLIENT.get(
                f"{BASE_URL}/assets/list?includeSeekKeys=true",
                headers={"User-Agent": USER_AGENT}
            )
    
        else:
            seek_key_value = None     
            r = await CLIENT.get(
                f"{BASE_URL}/assets/list",
                headers={"User-Agent": USER_AGENT}
            )
        
        r.raise_for_status()
        digest_assets = r.json()

        # If filtering by genome_digest, return only that digest's assets
        if genome_digest:  # Non-empty string check
            genome_digest = genome_digest.strip()  # Remove whitespace
            if genome_digest in digest_assets.keys():
                assets = digest_assets[genome_digest]
                return {
                    "status": "success",
                    "genome_digest": genome_digest,
                    "count": len(assets),
                    "assets": assets
                }
            else:
                # Digest not found
                available_digests = list(digest_assets.keys())[:5]
                return {
                    "status": "error",
                    "error": f"Genome digest '{genome_digest}' not found",
                    "requested_digest": genome_digest,
                    "available_digests_sample": available_digests
                }
        else:
            # Return all as a list of {digest, assets} objects
            assets = [
                {"digest": digest, "assets": asset_list}
                for digest, asset_list in digest_assets.items()
            ]
            return {
                "status": "success",
                "count": len(assets),
                "assets": assets
            }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "genome": genome_digest
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_search_assets(asset_name: str) -> dict:
    """
    Search for all genomes that have a specific asset name.
    
    Args:
        asset_name: Name of asset to search for (e.g., "fasta", "bwa_index", "kallisto_index")
    
    Returns:
        List of genomes with the specified asset
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/genomes/by_asset/{asset_name}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Asset name not found: {asset_name}"
            }
        
        r.raise_for_status()
        genomes = r.json()
        
        return {
            "status": "success",
            "asset_name": asset_name,
            "count": len(genomes),
            "genomes": genomes
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "asset_name": asset_name
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_asset_path(genome_digest: str, asset_name: str, seek_key: str, tag: str = "default", remote: str = "http") -> dict:
    """
    Get the access path for an asset (local, HTTP, S3, etc.).
    
    Args:
        genome_digest: Genome digest (e.g., "8baf9d24ad8f5678f0fe1f5b21a812d410755d49e3123158")
        asset_name: Asset name (e.g., "fasta", "bwa_index")
        seek_key: Seek key for the asset
        tag: Asset tag (default: "default")
        remote: Remote type to request (e.g., "http", "s3", "aws"). If None, returns default.
    
    Returns:
        Path or URL to the asset
    """
    try:
        # Build the path endpoint
        path = f"{BASE_URL}/assets/file_path/{genome_digest}/{asset_name}/{seek_key}?tag={tag}"
        
        # Add remote parameter if specified
        params = {}
        if remote:
            params["remoteClass"] = remote
        
        r = await CLIENT.get(
            path,
            params=params,
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Asset or path not found: {genome_digest}/{asset_name}/{seek_key}?tag={tag}"
            }
        
        r.raise_for_status()
        
        return {
            "status": "success",
            "genome": genome_digest,
            "asset": asset_name,
            "seek_key": seek_key,
            "tag": tag,
            "remote": remote,
            "path": r.text.strip() if r.text else r.json()
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
