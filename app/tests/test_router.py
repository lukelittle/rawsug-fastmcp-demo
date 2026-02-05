"""Tests for deterministic router."""

import pytest
from vinyl.router import DeterministicRouter, Intent


@pytest.fixture
def router():
    """Create router instance."""
    return DeterministicRouter()


def test_artist_query_intent(router):
    """Test artist query intent detection."""
    messages = [
        "what do i have by Grimes",
        "What records do I have by Pixies?",
        "show me Girl Talk",
        "records by Sufjan Stevens",
        "do i have any Grimes albums",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "query_vinyl_collection"
        assert result.tool_args["query_type"] == "artist"
        assert result.tool_args["search_term"]  # Should extract artist name


def test_label_query_intent(router):
    """Test label query intent detection."""
    messages = [
        "do i have anything on 4AD",
        "anything on the 4AD label",
        "records on Asthmatic Kitty Records",
        "what's on 4AD",
        "4AD releases",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "query_vinyl_collection"
        assert result.tool_args["query_type"] == "label"
        assert result.tool_args["search_term"]


def test_year_query_intent(router):
    """Test year query intent detection."""
    messages = [
        "records from 2016",
        "2020 releases",
        "stuff from 2012",
        "albums from 2015",
        "what do i have from 2018",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "query_vinyl_collection"
        assert result.tool_args["query_type"] == "year"
        assert result.tool_args["search_term"] in ["2016", "2020", "2012", "2015", "2018"]


def test_year_range_intent(router):
    """Test year range intent detection."""
    messages = [
        "between 2010 and 2020",
        "from 2015 to 2020",
        "2010-2015",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "filter_records"
        assert "year_from" in result.tool_args
        assert "year_to" in result.tool_args


def test_stats_intent(router):
    """Test stats intent detection."""
    messages = [
        "how many records",
        "collection stats",
        "give me a quick summary",
        "stats",
        "tell me about my collection",
        "what's in my collection",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "stats_summary"
        assert result.tool_args == {}


def test_list_artists_intent(router):
    """Test list artists intent detection."""
    messages = [
        "list artists",
        "show me all artists",
        "what artists do i have",
        "who's in my collection",
        "list all the artists",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "list_artists"


def test_search_all_intent(router):
    """Test general search intent detection."""
    messages = [
        "search for electronic",
        "find jazz",
        "look for ambient",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name == "query_vinyl_collection"
        assert result.tool_args["query_type"] == "all"


def test_unknown_intent_fallback(router):
    """Test fallback for unknown intents."""
    messages = [
        "hello",
        "what's the weather",
        "tell me a joke",
        "how are you",
    ]
    
    for message in messages:
        result = router.route(message)
        assert result.tool_name is None
        assert result.fallback_response is not None
        assert "example" in result.fallback_response.lower()


def test_case_insensitive_routing(router):
    """Test that routing is case-insensitive."""
    result1 = router.route("what do i have by grimes")
    result2 = router.route("WHAT DO I HAVE BY GRIMES")
    result3 = router.route("What Do I Have By Grimes")
    
    assert result1.tool_name == result2.tool_name == result3.tool_name
    assert result1.tool_args["query_type"] == result2.tool_args["query_type"] == result3.tool_args["query_type"]


def test_parameter_extraction_artist(router):
    """Test artist name extraction."""
    result = router.route("what do i have by Grimes")
    assert "grimes" in result.tool_args["search_term"].lower()
    
    result = router.route("show me Sufjan Stevens albums")
    assert "sufjan stevens" in result.tool_args["search_term"].lower()


def test_parameter_extraction_label(router):
    """Test label name extraction."""
    result = router.route("do i have anything on 4AD")
    assert "4ad" in result.tool_args["search_term"].lower()


def test_parameter_extraction_year_range(router):
    """Test year range extraction."""
    result = router.route("between 2010 and 2020")
    assert result.tool_args["year_from"] == 2010
    assert result.tool_args["year_to"] == 2020
    
    result = router.route("from 2015 to 2019")
    assert result.tool_args["year_from"] == 2015
    assert result.tool_args["year_to"] == 2019


def test_confidence_scores(router):
    """Test that confidence scores are reasonable."""
    # High confidence for clear intents
    result = router.route("give me stats")
    assert result.confidence >= 0.9
    
    # Lower confidence for search
    result = router.route("search electronic")
    assert result.confidence >= 0.5
    
    # Zero confidence for unknown
    result = router.route("hello world")
    assert result.confidence == 0.0
