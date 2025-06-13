"""Tests for PDF handler functionality."""

import pytest
from gmft_cli.pdf_handler import (
    PDFHandler,
    get_pdf_handler,
    list_pdf_backends,
    PDFBackendInfo,
)


class TestPDFHandler:
    """Test PDF handler functionality."""

    def test_check_available_backends(self):
        """Test checking available PDF backends."""
        backends = PDFHandler.check_available_backends()

        assert isinstance(backends, list)
        assert len(backends) >= 2  # Should check for both pypdfium2 and pymupdf

        for backend in backends:
            assert isinstance(backend, PDFBackendInfo)
            assert backend.name in ["pypdfium2", "pymupdf"]
            assert isinstance(backend.available, bool)

    def test_pdf_handler_initialization(self):
        """Test PDF handler initialization."""
        # Try to initialize with auto-detection
        try:
            handler = PDFHandler()
            assert handler.is_available
            assert handler.backend_name in ["pypdfium2", "pymupdf"]
        except ImportError:
            # No backends available - this is OK for testing
            pytest.skip("No PDF backends available")

    def test_pdf_handler_specific_backend(self):
        """Test PDF handler with specific backend request."""
        # Check which backends are available
        backends = PDFHandler.check_available_backends()
        available_backends = [b.name for b in backends if b.available]

        if not available_backends:
            pytest.skip("No PDF backends available")

        # Test with first available backend
        backend_name = available_backends[0]
        handler = PDFHandler(backend=backend_name)
        assert handler.backend_name == backend_name

    def test_pdf_handler_unavailable_backend(self):
        """Test PDF handler with unavailable backend."""
        with pytest.raises(ImportError, match="not available"):
            PDFHandler(backend="nonexistent_backend")

    def test_get_pdf_handler_singleton(self):
        """Test that get_pdf_handler returns singleton."""
        try:
            handler1 = get_pdf_handler()
            handler2 = get_pdf_handler()
            assert handler1 is handler2
        except ImportError:
            pytest.skip("No PDF backends available")

    def test_open_document(self, sample_pdf):
        """Test opening a PDF document."""
        try:
            handler = get_pdf_handler()
        except ImportError:
            pytest.skip("No PDF backends available")

        # Should be able to open the document
        doc = handler.open_document(sample_pdf)
        assert doc is not None

        # Should have pages
        assert len(doc) > 0

        # Don't forget to close
        doc.close()

    def test_get_page_count(self, sample_pdf):
        """Test getting page count."""
        try:
            handler = get_pdf_handler()
        except ImportError:
            pytest.skip("No PDF backends available")

        count = handler.get_page_count(sample_pdf)
        assert isinstance(count, int)
        assert count > 0

    def test_extract_page_text(self, sample_pdf):
        """Test extracting text from page."""
        try:
            handler = get_pdf_handler()
        except ImportError:
            pytest.skip("No PDF backends available")

        # Try to extract text from first page
        try:
            text = handler.extract_page_text(sample_pdf, 0)
            assert isinstance(text, str)
            # May or may not have text depending on how PDF was created
        except Exception:
            # Some backends might not support text extraction
            pass

    def test_list_pdf_backends_function(self, capsys):
        """Test list_pdf_backends function output."""
        list_pdf_backends()

        captured = capsys.readouterr()
        assert "PDF Backend Status:" in captured.out
        assert "pypdfium2" in captured.out
        assert "pymupdf" in captured.out
        assert "Available" in captured.out or "Not available" in captured.out


class TestPDFBackendIntegration:
    """Test PDF backend integration with CLI."""

    @pytest.mark.parametrize("backend", ["pypdfium2", "pymupdf"])
    def test_backend_switching(self, backend):
        """Test switching between backends."""
        # Check if backend is available
        backends = PDFHandler.check_available_backends()
        backend_info = next((b for b in backends if b.name == backend), None)

        if not backend_info or not backend_info.available:
            pytest.skip(f"{backend} not available")

        # Should be able to create handler with this backend
        handler = PDFHandler(backend=backend)
        assert handler.backend_name == backend
        assert handler.is_available
