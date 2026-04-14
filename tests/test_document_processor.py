import os
import tempfile
import pytest

from app.services.document_processor import (
    clean_text, 
    chunk_text, 
    extract_text_from_txt, 
    process_document
)

def test_clean_text_removes_spaces():
    """Test that clean_text removes multiple consecutive spaces."""
    assert clean_text("hello    world") == "hello world"
    
def test_clean_text_normalizes_whitespace():
    """Test that clean_text normalizes tabs and newlines to single space."""
    assert clean_text("hello\tworld\n!") == "hello world !"
    
def test_clean_text_strips_whitespace():
    """Test that clean_text strips leading and trailing whitespace."""
    assert clean_text("  hello world  ") == "hello world"
    
def test_clean_text_empty():
    """Test that clean_text returns empty string for empty or whitespace-only input."""
    assert clean_text("") == ""
    assert clean_text("   \n \t  ") == ""
    
def test_chunk_text_basic():
    """Test that chunk_text returns a list of (str, int) tuples."""
    text = "word " * 100
    chunks = chunk_text(text, page_number=1, chunk_size=20, chunk_overlap=5)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert isinstance(chunks[0], tuple)
    assert isinstance(chunks[0][0], str)
    assert isinstance(chunks[0][1], int)

def test_chunk_text_multiple_chunks():
    """Test that chunk_text produces multiple chunks with the correct overlap."""
    text = "word " * 100
    chunks = chunk_text(text, page_number=1, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > 1

def test_chunk_text_empty():
    """Test that chunk_text returns empty list for empty text input."""
    assert chunk_text("", 1) == []
    assert chunk_text("   ", 1) == []
    
def test_chunk_text_short():
    """Test that short text under chunk_size produces exactly one chunk."""
    text = "word " * 10
    chunks = chunk_text(text, page_number=1, chunk_size=20, chunk_overlap=5)
    assert len(chunks) == 1
    assert chunks[0][0].count("word") == 10
    
def test_extract_text_from_txt_basic():
    """Test extract_text_from_txt reads text and returns it with page number."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write("test content here")
        filepath = f.name
        
    try:
        pages = extract_text_from_txt(filepath)
        assert len(pages) == 1
        assert pages[0][0] == "test content here"
        assert pages[0][1] == 1
    finally:
        os.unlink(filepath)
        
def test_extract_text_from_txt_form_feed():
    """Test that with form-feed character, multiple pages are returned."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write("page 1\fpage 2\fpage 3")
        filepath = f.name
        
    try:
        pages = extract_text_from_txt(filepath)
        assert len(pages) == 3
        assert pages[0][0] == "page 1"
        assert pages[0][1] == 1
        assert pages[1][0] == "page 2"
        assert pages[1][1] == 2
        assert pages[2][0] == "page 3"
        assert pages[2][1] == 3
    finally:
        os.unlink(filepath)

def test_extract_text_from_txt_long():
    """Test that long content is split into blocks when no form-feed exists."""
    long_text = "a" * 4000
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write(long_text)
        filepath = f.name
        
    try:
        pages = extract_text_from_txt(filepath)
        assert len(pages) == 2
        assert len(pages[0][0]) == 3000
        assert len(pages[1][0]) == 1000
    finally:
        os.unlink(filepath)

def test_process_document_txt_success():
    """Test process_document processes a TXT file into chunks and counts pages."""
    text = "word " * 200
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write(text)
        filepath = f.name
        
    try:
        chunks, total_pages = process_document(filepath, file_type="txt", chunk_size=50, chunk_overlap=10)
        assert total_pages >= 1
        assert len(chunks) > 1
        for chunk_text_val, page_num in chunks:
            assert len(chunk_text_val) > 0
            assert page_num >= 1
    finally:
        os.unlink(filepath)
        
def test_process_document_unsupported_type():
    """Test process_document raises ValueError for unsupported types."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        process_document("dummy.xyz", "xyz")
        
def test_process_document_max_pages_truncation():
    """Test max_pages truncation logic."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
        f.write("p1\fp2\fp3\fp4\fp5")
        filepath = f.name
        
    try:
        chunks, total_pages = process_document(filepath, file_type="txt", max_pages=2)
        assert total_pages == 2
        
        page_nums = set([c[1] for c in chunks])
        assert page_nums == {1, 2}
    finally:
        os.unlink(filepath)
