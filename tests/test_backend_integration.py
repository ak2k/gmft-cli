"""Integration tests that verify both PDF backends work correctly with CLI commands."""

import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from gmft_cli.cli import cli
from gmft_cli.pdf_handler import PDFHandler


@pytest.mark.integration
class TestBackendIntegration:
    """Test that both PDF backends work correctly with CLI operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @pytest.mark.parametrize("backend", ["pypdfium2", "pymupdf"])
    def test_extract_with_backend(self, backend, sample_pdf):
        """Test extract command works with both backends."""
        # Check if backend is available
        backends = PDFHandler.check_available_backends()
        backend_info = next((b for b in backends if b.name == backend), None)

        if not backend_info or not backend_info.available:
            pytest.skip(f"{backend} not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                cli,
                [
                    "--pdf-backend", backend,
                    "extract", str(sample_pdf),
                    "-o", tmpdir,
                    "--format", "json"
                ]
            )
            
            # Should complete successfully (even if no tables found)
            assert result.exit_code == 0

    @pytest.mark.parametrize("backend", ["pypdfium2", "pymupdf"])
    def test_detect_with_backend(self, backend, sample_pdf):
        """Test detect command works with both backends."""
        # Check if backend is available
        backends = PDFHandler.check_available_backends()
        backend_info = next((b for b in backends if b.name == backend), None)

        if not backend_info or not backend_info.available:
            pytest.skip(f"{backend} not available")

        result = self.runner.invoke(
            cli,
            ["--pdf-backend", backend, "detect", str(sample_pdf)]
        )
        
        # Should complete successfully
        assert result.exit_code == 0

    @pytest.mark.parametrize("backend", ["pypdfium2", "pymupdf"])
    def test_bulk_extract_with_backend(self, backend, multiple_pdfs):
        """Test bulk-extract command works with both backends."""
        # Check if backend is available
        backends = PDFHandler.check_available_backends()
        backend_info = next((b for b in backends if b.name == backend), None)

        if not backend_info or not backend_info.available:
            pytest.skip(f"{backend} not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                cli,
                [
                    "--pdf-backend", backend,
                    "bulk-extract", 
                    *[str(pdf) for pdf in multiple_pdfs],
                    "-o", tmpdir,
                    "--format", "csv"
                ]
            )
            
            # Should complete successfully
            assert result.exit_code == 0

    def test_backend_preference_respected(self, sample_pdf):
        """Test that CLI respects backend preference."""
        available_backends = []
        backends = PDFHandler.check_available_backends()
        
        for backend in backends:
            if backend.available:
                available_backends.append(backend.name)
        
        if len(available_backends) < 1:
            pytest.skip("No PDF backends available")

        # Test with each available backend
        for backend in available_backends:
            result = self.runner.invoke(
                cli,
                ["--pdf-backend", backend, "pdf-backends"]
            )
            
            assert result.exit_code == 0
            assert f"Current backend: {backend}" in result.output

    def test_auto_backend_selection(self, sample_pdf):
        """Test automatic backend selection works."""
        result = self.runner.invoke(
            cli,
            ["--pdf-backend", "auto", "pdf-backends"]
        )
        
        # Should succeed and show some backend as current
        assert result.exit_code == 0
        assert "Current backend:" in result.output

    def test_backend_environment_variable(self, sample_pdf, monkeypatch):
        """Test that GMFT_PDF_BACKEND environment variable is respected."""
        # Check what backends are available
        backends = PDFHandler.check_available_backends()
        available_backends = [b.name for b in backends if b.available]
        
        if not available_backends:
            pytest.skip("No PDF backends available")

        # Test with each available backend
        for backend in available_backends:
            # Set environment variable
            monkeypatch.setenv("GMFT_PDF_BACKEND", backend)
            
            result = self.runner.invoke(cli, ["pdf-backends"])
            
            assert result.exit_code == 0
            assert f"Current backend: {backend}" in result.output


@pytest.mark.integration
class TestBackendPerformance:
    """Compare backend performance characteristics (when both are available)."""

    def test_backend_performance_comparison(self, sample_pdf):
        """Compare processing speed between backends (informational only)."""
        import time
        
        backends = PDFHandler.check_available_backends()
        available_backends = [b.name for b in backends if b.available]
        
        if len(available_backends) < 2:
            pytest.skip("Need at least 2 backends for comparison")

        performance_results = {}
        
        for backend in available_backends:
            handler = PDFHandler(backend=backend)
            
            # Time a simple operation
            start_time = time.time()
            page_count = handler.get_page_count(sample_pdf)
            doc = handler.open_document(sample_pdf)
            doc.close()
            end_time = time.time()
            
            performance_results[backend] = {
                'time': end_time - start_time,
                'page_count': page_count
            }

        # This is informational - we don't assert on performance
        # But we do verify both backends got the same page count
        page_counts = [r['page_count'] for r in performance_results.values()]
        assert len(set(page_counts)) == 1, "Backends should report same page count"

    def test_backend_feature_parity(self, sample_pdf):
        """Test that both backends support required features."""
        backends = PDFHandler.check_available_backends()
        available_backends = [b.name for b in backends if b.available]
        
        if len(available_backends) < 2:
            pytest.skip("Need at least 2 backends for feature comparison")

        for backend in available_backends:
            handler = PDFHandler(backend=backend)
            
            # All backends should support these basic operations
            assert handler.is_available
            assert handler.get_page_count(sample_pdf) > 0
            
            doc = handler.open_document(sample_pdf)
            assert doc is not None
            assert len(doc) > 0
            doc.close()