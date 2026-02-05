"""FastMCP tools for vinyl collection queries."""

import logging
import os
from typing import Literal, Optional

from fastmcp import FastMCP

from .discogs import DiscogsCollection

logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("vinyl-collection-chatbot")

# Global collection instance (cached within Lambda invocation)
_collection: Optional[DiscogsCollection] = None


def get_collection() -> DiscogsCollection:
    """
    Get or initialize the DiscogsCollection instance.

    Returns:
        DiscogsCollection instance

    Raises:
        ValueError: If required environment variables are missing
    """
    global _collection

    if _collection is None:
        bucket = os.environ.get('DISCOGS_BUCKET')
        key = os.environ.get('DISCOGS_KEY', 'discogs.csv')

        if not bucket:
            raise ValueError("DISCOGS_BUCKET environment variable is required")

        logger.info(f"Initializing collection from s3://{bucket}/{key}")
        _collection = DiscogsCollection(bucket, key)
        _collection.load()

    return _collection


@mcp.tool()
def query_vinyl_collection(
    query_type: Literal["artist", "title", "label", "year", "all"],
    search_term: str,
    limit: int = 10
) -> list[str]:
    """
    Query the vinyl collection by various criteria.

    Searches the collection for records matching the specified criteria.
    Case-insensitive matching is used for all text searches.

    Args:
        query_type: Type of query - artist, title, label, year, or all
        search_term: The term to search for
        limit: Maximum number of results to return (1-50, default 10)

    Returns:
        List of formatted record strings: "Artist - Title (Label, Year)"

    Examples:
        query_vinyl_collection("artist", "Grimes", 5)
        query_vinyl_collection("label", "4AD", 10)
        query_vinyl_collection("year", "2016", 20)
    """
    # Validate limit bounds
    limit = max(1, min(50, limit))

    try:
        collection = get_collection()
        records = collection.query(query_type, search_term, limit)

        # Format results
        return [collection._format_record(r) for r in records]

    except Exception as e:
        logger.error(f"Error querying collection: {e}", exc_info=True)
        return [f"Error: Unable to query collection - {str(e)}"]


@mcp.tool()
def list_artists(
    starts_with: Optional[str] = None,
    limit: int = 25
) -> list[str]:
    """
    List unique artists in the collection.

    Returns a sorted list of unique artist names. Optionally filter
    to artists starting with a specific string.

    Args:
        starts_with: Optional prefix to filter artists (case-insensitive)
        limit: Maximum number of artists to return (1-100, default 25)

    Returns:
        Sorted list of unique artist names

    Examples:
        list_artists()  # All artists
        list_artists("G", 10)  # Artists starting with G
    """
    # Validate limit bounds
    limit = max(1, min(100, limit))

    try:
        collection = get_collection()
        artists = collection.get_artists(starts_with, limit)
        return artists

    except Exception as e:
        logger.error(f"Error listing artists: {e}", exc_info=True)
        return [f"Error: Unable to list artists - {str(e)}"]


@mcp.tool()
def stats_summary() -> dict:
    """
    Get collection statistics summary.

    Returns comprehensive statistics about the vinyl collection including
    total records, unique artists and labels, year range, and top artists/labels.

    Returns:
        Dictionary with statistics:
        - total_records: Total number of records
        - unique_artists: Number of unique artists
        - unique_labels: Number of unique labels
        - year_min: Earliest release year (if available)
        - year_max: Latest release year (if available)
        - top_artists: List of {artist, count} for top 5 artists
        - top_labels: List of {label, count} for top 5 labels

    Example:
        stats_summary()
    """
    try:
        collection = get_collection()
        return collection.get_stats()

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return {
            "error": f"Unable to get collection stats - {str(e)}",
            "total_records": 0,
            "unique_artists": 0,
            "unique_labels": 0,
            "year_min": None,
            "year_max": None,
            "top_artists": [],
            "top_labels": []
        }


@mcp.tool()
def filter_records(
    artist: Optional[str] = None,
    label: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = 10
) -> list[str]:
    """
    Filter records by multiple criteria.

    Returns records matching ALL specified criteria. All filters are optional.
    Year range is inclusive on both ends.

    Args:
        artist: Filter by artist name (case-insensitive partial match)
        label: Filter by label name (case-insensitive partial match)
        year_from: Minimum release year (inclusive)
        year_to: Maximum release year (inclusive)
        limit: Maximum number of results (1-50, default 10)

    Returns:
        List of formatted record strings: "Artist - Title (Label, Year)"

    Examples:
        filter_records(label="4AD", year_from=2010, year_to=2020)
        filter_records(artist="Grimes")
    """
    # Validate limit bounds
    limit = max(1, min(50, limit))

    try:
        collection = get_collection()
        records = collection.filter_records(artist, label, year_from, year_to, limit)

        # Format results
        return [collection._format_record(r) for r in records]

    except Exception as e:
        logger.error(f"Error filtering records: {e}", exc_info=True)
        return [f"Error: Unable to filter records - {str(e)}"]
