"""Deterministic router for intent detection and tool selection."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Intent(Enum):
    """User intent types."""
    QUERY_ARTIST = "query_artist"
    QUERY_TITLE = "query_title"
    QUERY_LABEL = "query_label"
    QUERY_YEAR = "query_year"
    QUERY_YEAR_RANGE = "query_year_range"
    LIST_ARTISTS = "list_artists"
    STATS = "stats"
    SEARCH_ALL = "search_all"
    UNKNOWN = "unknown"


@dataclass
class RouterResult:
    """Result from routing a message."""
    tool_name: Optional[str]
    tool_args: Optional[dict]
    fallback_response: Optional[str]
    confidence: float


class DeterministicRouter:
    """Rules-based router for tool selection without LLM."""

    def __init__(self):
        """Initialize router with intent patterns."""
        # Artist query patterns
        self.artist_patterns = [
            r"what (?:do i have|records do i have|albums do i have) by (.+)",
            r"(?:show me|find|get) (.+?)(?:'s)? (?:records|albums|music)",
            r"records by (.+)",
            r"albums by (.+)",
            r"(?:do i have|got) (?:any )?(.+?) (?:records|albums)",
            r"show me (.+)",
        ]

        # Label query patterns
        self.label_patterns = [
            r"(?:do i have )?anything on (?:the )?(.+?)(?:\s+label)?$",
            r"records on (?:the )?(.+?)(?:\s+label)?$",
            r"what(?:'s| is) on (?:the )?(.+?)(?:\s+label)?$",
            r"^(.+?)\s+releases$",
        ]

        # Year query patterns
        self.year_patterns = [
            r"(?:records|albums|stuff) from (\d{4})",
            r"(\d{4}) (?:releases|records|albums)",
            r"what (?:do i have|records) from (\d{4})",
        ]

        # Year range patterns
        self.year_range_patterns = [
            r"between (\d{4}) and (\d{4})",
            r"from (\d{4}) to (\d{4})",
            r"(\d{4})\s*-\s*(\d{4})",
        ]

        # Stats patterns
        self.stats_patterns = [
            r"how many records",
            r"collection stats",
            r"(?:give me a )?(?:quick )?(?:stats|statistics|summary)",
            r"tell me about my collection",
            r"what(?:'s| is) in my collection",
        ]

        # List artists patterns
        self.list_artists_patterns = [
            r"list (?:all )?(?:the )?artists",
            r"show (?:me )?(?:all )?(?:the )?artists",
            r"what artists (?:do i have)?",
            r"who(?:'s| is) in my collection",
        ]

        # Search patterns
        self.search_patterns = [
            r"search (?:for )?(.+)",
            r"find (.+)",
            r"look for (.+)",
        ]

    def route(self, message: str) -> RouterResult:
        """
        Analyze message and determine tool + parameters.

        Args:
            message: User's natural language message

        Returns:
            RouterResult with tool_name, tool_args, or fallback_response
        """
        message_lower = message.lower().strip()

        # Detect intent
        intent, extracted_params = self._detect_intent(message_lower)

        # Route based on intent
        if intent == Intent.QUERY_ARTIST:
            return RouterResult(
                tool_name="query_vinyl_collection",
                tool_args={
                    "query_type": "artist",
                    "search_term": extracted_params.get("search_term", ""),
                    "limit": 10
                },
                fallback_response=None,
                confidence=0.9
            )

        elif intent == Intent.QUERY_LABEL:
            return RouterResult(
                tool_name="query_vinyl_collection",
                tool_args={
                    "query_type": "label",
                    "search_term": extracted_params.get("search_term", ""),
                    "limit": 10
                },
                fallback_response=None,
                confidence=0.9
            )

        elif intent == Intent.QUERY_YEAR:
            return RouterResult(
                tool_name="query_vinyl_collection",
                tool_args={
                    "query_type": "year",
                    "search_term": extracted_params.get("year", ""),
                    "limit": 10
                },
                fallback_response=None,
                confidence=0.9
            )

        elif intent == Intent.QUERY_YEAR_RANGE:
            return RouterResult(
                tool_name="filter_records",
                tool_args={
                    "year_from": extracted_params.get("year_from"),
                    "year_to": extracted_params.get("year_to"),
                    "limit": 10
                },
                fallback_response=None,
                confidence=0.9
            )

        elif intent == Intent.STATS:
            return RouterResult(
                tool_name="stats_summary",
                tool_args={},
                fallback_response=None,
                confidence=0.95
            )

        elif intent == Intent.LIST_ARTISTS:
            return RouterResult(
                tool_name="list_artists",
                tool_args={"limit": 25},
                fallback_response=None,
                confidence=0.9
            )

        elif intent == Intent.SEARCH_ALL:
            return RouterResult(
                tool_name="query_vinyl_collection",
                tool_args={
                    "query_type": "all",
                    "search_term": extracted_params.get("search_term", ""),
                    "limit": 10
                },
                fallback_response=None,
                confidence=0.7
            )

        else:
            # Unknown intent - return fallback
            return RouterResult(
                tool_name=None,
                tool_args=None,
                fallback_response=self._generate_fallback(),
                confidence=0.0
            )

    def _detect_intent(self, message: str) -> tuple[Intent, dict]:
        """
        Detect user intent from message.

        Args:
            message: Normalized message (lowercase)

        Returns:
            Tuple of (Intent, extracted_params dict)
        """
        # Check year range first (more specific)
        for pattern in self.year_range_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                year_from = int(match.group(1))
                year_to = int(match.group(2))
                return Intent.QUERY_YEAR_RANGE, {
                    "year_from": year_from,
                    "year_to": year_to
                }

        # Check stats patterns
        for pattern in self.stats_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return Intent.STATS, {}

        # Check list artists patterns
        for pattern in self.list_artists_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return Intent.LIST_ARTISTS, {}

        # Check year patterns (before label patterns to avoid "2020 releases" matching label)
        for pattern in self.year_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                year = match.group(1)
                return Intent.QUERY_YEAR, {"year": year}

        # Check artist patterns
        for pattern in self.artist_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                artist = match.group(1).strip()
                # Clean up common trailing words
                artist = re.sub(r'\s+(records|albums|music|stuff)$', '', artist, flags=re.IGNORECASE)
                return Intent.QUERY_ARTIST, {"search_term": artist}

        # Check label patterns
        for pattern in self.label_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                label = match.group(1).strip()
                return Intent.QUERY_LABEL, {"search_term": label}

        # Check search patterns
        for pattern in self.search_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                search_term = match.group(1).strip()
                return Intent.SEARCH_ALL, {"search_term": search_term}

        # No match
        return Intent.UNKNOWN, {}

    def _generate_fallback(self) -> str:
        """
        Generate polite fallback response for unknown intents.

        Returns:
            Fallback message with example queries
        """
        return (
            "I'm not sure what you're looking for. Here are some example queries:\n\n"
            "• \"What records do I have by Grimes?\"\n"
            "• \"Do I have anything on 4AD?\"\n"
            "• \"Show me records from 2016\"\n"
            "• \"Records between 2010 and 2020\"\n"
            "• \"Give me a quick stats summary\"\n"
            "• \"List some artists\"\n"
            "• \"Search for electronic\""
        )
