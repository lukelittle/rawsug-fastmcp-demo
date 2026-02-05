"""Tests for Discogs CSV reader."""

import io
import pytest
from moto import mock_aws
import boto3

from vinyl.discogs import DiscogsCollection


@mock_aws
def test_load_csv_from_s3(sample_csv_content):
    """Test loading CSV from S3."""
    # Create mock S3 bucket and upload CSV
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    # Test loading
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    assert collection._records is not None
    assert len(collection._records) > 0


@mock_aws
def test_query_by_artist(sample_csv_content):
    """Test querying by artist name."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Query for Grimes
    results = collection.query('artist', 'Grimes', limit=10)
    
    assert len(results) > 0
    for record in results:
        assert 'grimes' in record.get('Artist', '').lower()


@mock_aws
def test_query_case_insensitive(sample_csv_content):
    """Test case-insensitive search."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Query with different cases
    results_lower = collection.query('artist', 'grimes', limit=10)
    results_upper = collection.query('artist', 'GRIMES', limit=10)
    results_mixed = collection.query('artist', 'Grimes', limit=10)
    
    assert len(results_lower) == len(results_upper) == len(results_mixed)


@mock_aws
def test_query_by_label(sample_csv_content):
    """Test querying by label."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Query for 4AD label
    results = collection.query('label', '4AD', limit=10)
    
    assert len(results) > 0
    for record in results:
        assert '4ad' in record.get('Label', '').lower()


@mock_aws
def test_query_by_year(sample_csv_content):
    """Test querying by year."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Query for 2020
    results = collection.query('year', '2020', limit=10)
    
    assert len(results) > 0


@mock_aws
def test_get_stats(sample_csv_content):
    """Test collection statistics."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Get stats
    stats = collection.get_stats()
    
    assert 'total_records' in stats
    assert 'unique_artists' in stats
    assert 'unique_labels' in stats
    assert 'year_min' in stats
    assert 'year_max' in stats
    assert 'top_artists' in stats
    assert 'top_labels' in stats
    
    assert stats['total_records'] > 0
    assert stats['unique_artists'] > 0
    assert stats['unique_labels'] > 0


@mock_aws
def test_list_artists(sample_csv_content):
    """Test listing artists."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Get all artists
    artists = collection.get_artists(limit=100)
    
    assert len(artists) > 0
    # Check sorted
    assert artists == sorted(artists)
    # Check unique
    assert len(artists) == len(set(artists))


@mock_aws
def test_filter_records(sample_csv_content):
    """Test filtering records by multiple criteria."""
    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    
    s3.put_object(Bucket='test-bucket', Key='discogs.csv', Body=sample_csv_content)
    
    collection = DiscogsCollection('test-bucket', 'discogs.csv')
    collection.load()
    
    # Filter by label and year range
    results = collection.filter_records(
        label='4AD',
        year_from=2010,
        year_to=2020,
        limit=10
    )
    
    # All results should match criteria
    for record in results:
        assert '4ad' in record.get('Label', '').lower()
        year = collection._parse_year(record.get('Released', ''))
        if year:
            assert 2010 <= year <= 2020
