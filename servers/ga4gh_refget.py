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


def canonicalize(seq: str) -> str:
    """Canonicalize sequence: remove non-letters, convert to uppercase."""
    return re.sub(r"[^A-Za-z]", "", seq).upper()


def md5(seq: str) -> str:
    """Compute MD5 digest of sequence."""
    return hashlib.md5(canonicalize(seq).encode()).hexdigest()


def ga4gh_digest(seq: str) -> str:
    """Compute GA4GH digest (SQ.* format) of sequence."""
    sha = hashlib.sha512(canonicalize(seq).encode()).digest()
    return "SQ." + base64.urlsafe_b64encode(sha[:24]).decode().rstrip("=")


def sha256_digest(seq: str) -> str:
    """Compute SHA256 digest of sequence."""
    return "sha256:" + hashlib.sha256(canonicalize(seq).encode()).hexdigest()


def validate_fasta(content: str) -> bool:
    """Check if content looks like FASTA."""
    return content.strip().startswith(">")


def parse_fasta(content: str) -> list:
    """Parse FASTA format and return list of (header, sequence) tuples."""
    seqs = []
    header = None
    buf = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith(">"):
            if header:
                seqs.append((header, "".join(buf)))
            header = line[1:]
            buf = []
        else:
            buf.append(line)

    if header:
        seqs.append((header, "".join(buf)))

    return seqs


@mcp.tool()
async def refget_search(url: str, query: str, limit: int = 5) -> dict:
    """
    Search sequence collections from refget server.
    
    Args:
        url: Base URL of the refget server (e.g., https://seqcolapi.databio.org)
        query: Search query (e.g., "GRCh38", "human")
        limit: Maximum number of results to return
    
    Returns:
        List of matching collections
    """
    try:
        r = await CLIENT.get(
            f"{url}/api/v1/collections",
            params={"q": query, "limit": limit},
            headers={"User-Agent": USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
        return {
            "status": "success",
            "query": query,
            "count": len(data.get("collections", [])),
            "collections": data.get("collections", [])
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "url": f"{url}/api/v1/collections"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_get_collection(url: str, digest: str) -> dict:
    """
    Fetch a sequence collection by digest.
    
    Args:
        url: Base URL of the refget server (e.g., https://seqcolapi.databio.org)
        digest: Collection digest (e.g., "sha256:abc123...")
    
    Returns:
        Collection metadata and sequence information
    """
    try:
        r = await CLIENT.get(
            f"{url}/api/v1/collections/{digest}",
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


@mcp.tool()
async def refget_get_sequence(url: str, digest: str, start: Optional[int] = None, end: Optional[int] = None) -> dict:
    """
    Retrieve sequence by digest.
    
    Args:
        url: Base URL of the refget server (e.g., https://seqcolapi.databio.org)
        digest: Sequence digest (e.g., "sha256:abc123..." or "SQ...")
        start: Start position (0-based, inclusive, optional)
        end: End position (0-based, exclusive, optional)
    
    Returns:
        Sequence data with metadata
    """
    try:
        params = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        
        r = await CLIENT.get(
            f"{url}/api/v1/sequence/{digest}",
            params=params,
            headers={"User-Agent": USER_AGENT}
        )
        
        if r.status_code == 404:
            return {
                "status": "error",
                "error": "Sequence not found",
                "digest": digest
            }
        
        r.raise_for_status()
        sequence = r.text
        
        return {
            "status": "success",
            "digest": digest,
            "start": start,
            "end": end,
            "length": len(sequence),
            "sequence": sequence
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "digest": digest
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_compute_digests(sequence: str, name: str = "") -> dict:
    """
    Compute multiple digest formats for a sequence.
    
    Args:
        sequence: DNA/RNA sequence string
        name: Optional name for the sequence
    
    Returns:
        Sequence with MD5, GA4GH, and SHA256 digests
    """
    try:
        seq = canonicalize(sequence)
        if not seq:
            return {
                "status": "error",
                "error": "Sequence is empty or contains only non-letter characters"
            }
        
        return {
            "status": "success",
            "name": name,
            "length": len(seq),
            "digests": {
                "md5": md5(sequence),
                "ga4gh": ga4gh_digest(sequence),
                "sha256": sha256_digest(sequence)
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_verify_sequence(sequence: str, digest: str) -> dict:
    """
    Verify that a sequence matches a given digest.
    
    Args:
        sequence: DNA/RNA sequence string
        digest: Digest to verify against (MD5, GA4GH, or SHA256 format)
    
    Returns:
        Verification result with match status and computed digests
    """
    try:
        seq = canonicalize(sequence)
        if not seq:
            return {
                "status": "error",
                "error": "Sequence is empty or contains only non-letter characters"
            }
        
        computed_digests = {
            "md5": md5(sequence),
            "ga4gh": ga4gh_digest(sequence),
            "sha256": sha256_digest(sequence)
        }
        
        # Check which format the provided digest is and verify
        digest_lower = digest.lower()
        is_valid = False
        digest_type = None
        
        if digest_lower.startswith("sq."):
            is_valid = computed_digests["ga4gh"] == digest
            digest_type = "ga4gh"
        elif digest_lower.startswith("sha256:"):
            is_valid = computed_digests["sha256"] == digest
            digest_type = "sha256"
        elif len(digest) == 32 and all(c in "0123456789abcdef" for c in digest_lower):
            is_valid = computed_digests["md5"].lower() == digest_lower
            digest_type = "md5"
        else:
            return {
                "status": "error",
                "error": f"Unknown digest format: {digest}",
                "digest": digest
            }
        
        return {
            "status": "success",
            "valid": is_valid,
            "digest_type": digest_type,
            "provided_digest": digest,
            "sequence_length": len(seq),
            "computed_digests": computed_digests
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_process_fasta(fasta_content: str, name: str = "collection") -> dict:
    """
    Process FASTA content and compute digests for all sequences.
    
    Args:
        fasta_content: FASTA formatted sequence content
        name: Name for the collection
    
    Returns:
        Collection data with computed digests for all sequences
    """
    try:
        if not validate_fasta(fasta_content):
            return {
                "status": "error",
                "error": "Invalid FASTA format. Content must start with '>'"
            }
        
        parsed = parse_fasta(fasta_content)
        if not parsed:
            return {
                "status": "error",
                "error": "No sequences found in FASTA content"
            }
        
        sequences = []
        for seq_name, seq in parsed:
            sequences.append({
                "name": seq_name,
                "length": len(seq),
                "digests": {
                    "md5": md5(seq),
                    "ga4gh": ga4gh_digest(seq),
                    "sha256": sha256_digest(seq)
                }
            })
        
        return {
            "status": "success",
            "name": name,
            "num_sequences": len(sequences),
            "sequences": sequences
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_list_digests(sequence: str) -> dict:
    """
    List all available digest formats for a sequence.
    
    Args:
        sequence: DNA/RNA sequence string
    
    Returns:
        All digest formats with their values
    """
    try:
        seq = canonicalize(sequence)
        if not seq:
            return {
                "status": "error",
                "error": "Sequence is empty or contains only non-letter characters"
            }
        
        return {
            "status": "success",
            "canonical_sequence": seq,
            "length": len(seq),
            "digests": {
                "md5": md5(sequence),
                "ga4gh": ga4gh_digest(sequence),
                "sha256": sha256_digest(sequence),
            },
            "formats": {
                "md5": "32 character hex string",
                "ga4gh": "SQ.* format (GA4GH standard)",
                "sha256": "sha256:* format"
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def refget_batch_compute(sequences: str) -> dict:
    """
    Batch compute digests for multiple sequences (one per line).
    
    Args:
        sequences: Newline-separated sequences
    
    Returns:
        List of sequences with their digests
    """
    try:
        seq_list = [s.strip() for s in sequences.strip().split("\n") if s.strip()]
        if not seq_list:
            return {
                "status": "error",
                "error": "No sequences provided"
            }
        
        results = []
        for seq in seq_list:
            results.append({
                "length": len(canonicalize(seq)),
                "digests": {
                    "md5": md5(seq),
                    "ga4gh": ga4gh_digest(seq),
                    "sha256": sha256_digest(seq)
                }
            })
        
        return {
            "status": "success",
            "count": len(results),
            "sequences": results
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
