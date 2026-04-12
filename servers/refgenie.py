from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

# Initialize FastMCP server
mcp = FastMCP("refgenie")

# Constants
USER_AGENT = "refgenie-mcp/2.0"
# Get base URL from environment variable or use default
BASE_URL = os.getenv("REFGENIE_URL", "http://refgenomes.databio.org")
# API version
API_VERSION = "v3"
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
        "api_version": API_VERSION
    }


@mcp.tool()
async def refgenie_get_url() -> dict:
    """
    Get the current refgenie server URL and configuration.
    
    Returns:
        Current URL, API version, and server information
    """
    try:
        # Try to get server info
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/serverinfo",
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
        "api_version": API_VERSION,
        "user_agent": USER_AGENT,
        "timeout": TIMEOUT,
        "server_info": server_info
    }


@mcp.tool()
async def refgenie_list_genomes(organism: Optional[str] = None) -> dict:
    """
    List all available genomes on the refgenie server.
    
    Args:
        organism: Optional filter by organism name (e.g., "Homo sapiens")
    
    Returns:
        List of available genomes with metadata
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes",
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
        
        genomes = data.get("genomes", [])
        
        # Filter by organism if provided
        if organism:
            genomes = [g for g in genomes if organism.lower() in str(g).lower()]
        
        return {
            "status": "success",
            "count": len(genomes),
            "genomes": genomes,
            "organism_filter": organism
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
    Get detailed information about a specific genome.
    
    Args:
        genome_alias: Genome identifier or alias (e.g., "hg38", "mm10", "human_repeats")
    
    Returns:
        Detailed genome metadata including digest, organism, species, etc.
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/{genome_alias}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Genome not found: {genome_alias}"
            }
        
        r.raise_for_status()
        return {
            "status": "success",
            "genome": r.json(),
            "genome_alias": genome_alias
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
    Get the GA4GH digest for a genome by its alias.
    
    Args:
        genome_alias: Genome identifier or alias (e.g., "hg38", "mm10")
    
    Returns:
        GA4GH digest for the genome
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/genome_digest/{genome_alias}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Genome not found: {genome_alias}"
            }
        
        r.raise_for_status()
        data = r.json()
        
        return {
            "status": "success",
            "genome_alias": genome_alias,
            "digest": data.get("digest") or data,
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
async def refgenie_list_assets(genome_alias: str) -> dict:
    """
    List all available assets for a specific genome.
    
    Args:
        genome_alias: Genome identifier (e.g., "hg38", "mm10")
    
    Returns:
        List of available assets and their properties
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/{genome_alias}/assets",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Genome not found: {genome_alias}"
            }
        
        r.raise_for_status()
        data = r.json()
        assets = data.get("assets", []) if isinstance(data, dict) else data
        
        return {
            "status": "success",
            "genome": genome_alias,
            "count": len(assets) if isinstance(assets, list) else len(assets.get("assets", [])) if isinstance(assets, dict) else 0,
            "assets": assets
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "genome": genome_alias
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_asset(genome_alias: str, asset_name: str, tag: str = "default") -> dict:
    """
    Get detailed information about a specific genome asset.
    
    Args:
        genome_alias: Genome identifier (e.g., "hg38")
        asset_name: Asset name (e.g., "fasta", "bwa_index", "bowtie2_index")
        tag: Asset tag version (default: "default")
    
    Returns:
        Asset metadata including files, checksums, and paths
    """
    try:
        # Try endpoint with tag
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/{genome_alias}/assets/{asset_name}/{tag}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            # Try without tag
            r = await CLIENT.get(
                f"{BASE_URL}/api/{API_VERSION}/genomes/{genome_alias}/assets/{asset_name}",
                headers={"User-Agent": USER_AGENT}
            )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Asset not found: {genome_alias}/{asset_name}"
            }
        
        r.raise_for_status()
        return {
            "status": "success",
            "genome": genome_alias,
            "asset": asset_name,
            "tag": tag,
            "asset_data": r.json()
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "genome": genome_alias,
            "asset": asset_name
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_search_assets(asset_type: str) -> dict:
    """
    Search for all genomes that have a specific asset type.
    
    Args:
        asset_type: Type of asset to search for (e.g., "fasta", "bwa_index", "kallisto_index")
    
    Returns:
        List of genomes with the specified asset
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/assets/{asset_type}",
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Asset type not found: {asset_type}"
            }
        
        r.raise_for_status()
        data = r.json()
        genomes = data.get("genomes", [])
        
        return {
            "status": "success",
            "asset_type": asset_type,
            "count": len(genomes),
            "genomes": genomes
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "asset_type": asset_type
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_asset_path(genome_alias: str, asset_name: str, tag: str = "default", remote: Optional[str] = None) -> dict:
    """
    Get the access path for an asset (local, HTTP, S3, etc.).
    
    Args:
        genome_alias: Genome identifier (e.g., "hg38")
        asset_name: Asset name (e.g., "fasta", "bwa_index")
        tag: Asset tag (default: "default")
        remote: Remote type to request (e.g., "http", "s3", "aws"). If None, returns default.
    
    Returns:
        Path or URL to the asset
    """
    try:
        # Build the path endpoint
        path = f"{BASE_URL}/api/{API_VERSION}/genomes/{genome_alias}/assets/{asset_name}/{tag}/path"
        
        # Add remote parameter if specified
        params = {}
        if remote:
            params["remote"] = remote
        
        r = await CLIENT.get(
            path,
            params=params,
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": f"Asset or path not found: {genome_alias}/{asset_name}/{tag}"
            }
        
        r.raise_for_status()
        
        return {
            "status": "success",
            "genome": genome_alias,
            "asset": asset_name,
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


@mcp.tool()
async def refgenie_get_available_remotes() -> dict:
    """
    Get list of available remote storage systems on the server.
    
    Returns:
        Available remote types (http, s3, aws, gcs, etc.)
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/remotes/dict",
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        
        return {
            "status": "success",
            "remotes": r.json()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_server_summary() -> dict:
    """
    Get a summary of the refgenie server with statistics and supported features.
    
    Returns:
        Server summary including genome count, asset count, and supported features
    """
    try:
        # Get genomes
        genomes_r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes",
            headers={"User-Agent": USER_AGENT}
        )
        genomes_r.raise_for_status()
        genomes = genomes_r.json().get("genomes", [])
        
        # Get server info if available
        info_r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/serverinfo",
            headers={"User-Agent": USER_AGENT}
        )
        server_info = info_r.json() if info_r.status_code == 200 else None
        
        return {
            "status": "success",
            "server_url": BASE_URL,
            "api_version": API_VERSION,
            "genome_count": len(genomes),
            "genomes": genomes[:10],  # First 10 genomes
            "server_info": server_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_get_organism_genomes(organism: str) -> dict:
    """
    Get all genomes available for a specific organism.
    
    Args:
        organism: Organism name (e.g., "Homo sapiens", "Mus musculus", "human")
    
    Returns:
        List of genomes for the organism with available assets
    """
    try:
        r = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes",
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        all_genomes = r.json().get("genomes", [])
        
        # Filter by organism
        matching = []
        organism_lower = organism.lower()
        
        for genome in all_genomes:
            genome_str = str(genome).lower()
            if organism_lower in genome_str:
                matching.append(genome)
        
        return {
            "status": "success",
            "organism": organism,
            "count": len(matching),
            "genomes": matching
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refgenie_compare_genomes(genome1: str, genome2: str) -> dict:
    """
    Compare assets available for two genomes.
    
    Args:
        genome1: First genome identifier
        genome2: Second genome identifier
    
    Returns:
        Comparison of assets between the two genomes
    """
    try:
        # Get assets for both genomes
        r1 = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/{genome1}/assets",
            headers={"User-Agent": USER_AGENT}
        )
        r2 = await CLIENT.get(
            f"{BASE_URL}/api/{API_VERSION}/genomes/{genome2}/assets",
            headers={"User-Agent": USER_AGENT}
        )
        
        r1.raise_for_status()
        r2.raise_for_status()
        
        assets1 = r1.json().get("assets", []) if isinstance(r1.json(), dict) else r1.json()
        assets2 = r2.json().get("assets", []) if isinstance(r2.json(), dict) else r2.json()
        
        # Convert to lists if needed and extract names
        def get_asset_names(assets):
            if isinstance(assets, list):
                return [a.get("name") if isinstance(a, dict) else str(a) for a in assets]
            elif isinstance(assets, dict):
                return list(assets.keys())
            return []
        
        names1 = set(get_asset_names(assets1))
        names2 = set(get_asset_names(assets2))
        
        return {
            "status": "success",
            "genome1": genome1,
            "genome2": genome2,
            "assets_in_genome1": len(names1),
            "assets_in_genome2": len(names2),
            "common_assets": list(names1 & names2),
            "unique_to_genome1": list(names1 - names2),
            "unique_to_genome2": list(names2 - names1)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
