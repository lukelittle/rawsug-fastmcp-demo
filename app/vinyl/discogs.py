"""Discogs CSV reader and collection manager."""

import csv
import io
import logging
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DiscogsCollection:
    """Manages Discogs CSV data from S3."""

    def __init__(self, bucket: str, key: str):
        """
        Initialize collection manager.

        Args:
            bucket: S3 bucket name containing the CSV
            key: S3 object key for the CSV file
        """
        self.bucket = bucket
        self.key = key
        self._records: Optional[list[dict]] = None
        self._s3_client = boto3.client('s3')

    def load(self) -> None:
        """
        Download and parse CSV from S3.

        Raises:
            ClientError: If S3 access fails
            csv.Error: If CSV parsing fails
        """
        try:
            logger.info(f"Loading CSV from s3://{self.bucket}/{self.key}")
            response = self._s3_client.get_object(Bucket=self.bucket, Key=self.key)
            csv_content = response['Body'].read().decode('utf-8')

            # Parse CSV
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            self._records = list(reader)

            logger.info(f"Loaded {len(self._records)} records from CSV")

        except ClientError as e:
            logger.error(f"Failed to load CSV from S3: {e}", exc_info=True)
            raise
        except csv.Error as e:
            logger.error(f"Failed to parse CSV: {e}", exc_info=True)
            raise

    def _normalize(self, value: str) -> str:
        """
        Normalize string for case-insensitive comparison.

        Args:
            value: String to normalize

        Returns:
            Normalized string (stripped and lowercased)
        """
        if not value:
            return ""
        return value.strip().lower()

    def _parse_year(self, released: str) -> Optional[int]:
        """
        Extract year from Released field.

        Args:
            released: Released field value (may contain year)

        Returns:
            Parsed year as integer, or None if not found
        """
        if not released:
            return None

        # Try to extract 4-digit year
        match = re.search(r'\b(19\d{2}|20\d{2})\b', released)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

        return None

    def _format_record(self, record: dict) -> str:
        """
        Format record as display string.

        Args:
            record: Record dictionary

        Returns:
            Formatted string: "Artist - Title (Label, Year)"
        """
        artist = record.get('Artist', 'Unknown Artist')
        title = record.get('Title', 'Unknown Title')
        label = record.get('Label', 'Unknown Label')
        released = record.get('Released', '')

        return f"{artist} - {title} ({label}, {released})"

    def _ensure_loaded(self) -> None:
        """Ensure CSV is loaded before querying."""
        if self._records is None:
            self.load()

    def query(
        self,
        query_type: str,
        search_term: str,
        limit: int = 10
    ) -> list[dict]:
        """
        Query records by type and term.

        Args:
            query_type: One of artist, title, label, year, all
            search_term: Term to search for
            limit: Maximum results

        Returns:
            List of matching record dicts
        """
        self._ensure_loaded()

        normalized_term = self._normalize(search_term)
        results = []

        for record in self._records:
            match = False

            if query_type == "artist":
                artist = self._normalize(record.get('Artist', ''))
                # Support searching with or without disambiguation numbers
                # e.g., "Grimes" matches "Grimes (4)"
                if normalized_term in artist or artist.startswith(normalized_term + " ("):
                    match = True

            elif query_type == "title":
                title = self._normalize(record.get('Title', ''))
                if normalized_term in title:
                    match = True

            elif query_type == "label":
                label = self._normalize(record.get('Label', ''))
                if normalized_term in label:
                    match = True

            elif query_type == "year":
                year = self._parse_year(record.get('Released', ''))
                if year and str(year) == search_term:
                    match = True

            elif query_type == "all":
                artist = self._normalize(record.get('Artist', ''))
                title = self._normalize(record.get('Title', ''))
                label = self._normalize(record.get('Label', ''))
                if (normalized_term in artist or
                    normalized_term in title or
                    normalized_term in label):
                    match = True

            if match:
                results.append(record)
                if len(results) >= limit:
                    break

        return results

    def filter_records(
        self,
        artist: Optional[str] = None,
        label: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Filter records by multiple criteria.

        Args:
            artist: Filter by artist name (partial match)
            label: Filter by label name (partial match)
            year_from: Minimum release year (inclusive)
            year_to: Maximum release year (inclusive)
            limit: Maximum results

        Returns:
            List of matching record dicts
        """
        self._ensure_loaded()

        results = []
        normalized_artist = self._normalize(artist) if artist else None
        normalized_label = self._normalize(label) if label else None

        for record in self._records:
            # Check all criteria (AND logic)
            match = True

            if normalized_artist:
                record_artist = self._normalize(record.get('Artist', ''))
                if normalized_artist not in record_artist:
                    match = False

            if normalized_label:
                record_label = self._normalize(record.get('Label', ''))
                if normalized_label not in record_label:
                    match = False

            if year_from is not None or year_to is not None:
                year = self._parse_year(record.get('Released', ''))
                if year is None:
                    match = False
                else:
                    if year_from is not None and year < year_from:
                        match = False
                    if year_to is not None and year > year_to:
                        match = False

            if match:
                results.append(record)
                if len(results) >= limit:
                    break

        return results

    def get_artists(
        self,
        starts_with: Optional[str] = None,
        limit: int = 25
    ) -> list[str]:
        """
        Get unique artist names.

        Args:
            starts_with: Optional prefix to filter artists
            limit: Maximum number of artists

        Returns:
            Sorted list of unique artist names
        """
        self._ensure_loaded()

        artists = set()
        normalized_prefix = self._normalize(starts_with) if starts_with else None

        for record in self._records:
            artist = record.get('Artist', '').strip()
            if not artist:
                continue

            if normalized_prefix:
                if self._normalize(artist).startswith(normalized_prefix):
                    artists.add(artist)
            else:
                artists.add(artist)

        # Sort and limit
        sorted_artists = sorted(artists)
        return sorted_artists[:limit]

    def get_stats(self) -> dict:
        """
        Calculate collection statistics.

        Returns:
            Dictionary with statistics:
            - total_records: Total number of records
            - unique_artists: Number of unique artists
            - unique_labels: Number of unique labels
            - year_min: Earliest release year (if available)
            - year_max: Latest release year (if available)
            - top_artists: List of {artist, count} for top 5 artists
            - top_labels: List of {label, count} for top 5 labels
        """
        self._ensure_loaded()

        # Count artists and labels
        artist_counts = {}
        label_counts = {}
        years = []

        for record in self._records:
            # Count artists
            artist = record.get('Artist', '').strip()
            if artist:
                artist_counts[artist] = artist_counts.get(artist, 0) + 1

            # Count labels
            label = record.get('Label', '').strip()
            if label:
                label_counts[label] = label_counts.get(label, 0) + 1

            # Collect years
            year = self._parse_year(record.get('Released', ''))
            if year:
                years.append(year)

        # Top artists
        top_artists = sorted(
            [{"artist": k, "count": v} for k, v in artist_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        # Top labels
        top_labels = sorted(
            [{"label": k, "count": v} for k, v in label_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        return {
            "total_records": len(self._records),
            "unique_artists": len(artist_counts),
            "unique_labels": len(label_counts),
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
            "top_artists": top_artists,
            "top_labels": top_labels
        }
