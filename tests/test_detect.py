"""Tests for the detect command."""

import pytest
from gmft_cli.cli import cli


class TestDetectCommand:
    """Test the detect command functionality."""

    def test_detect_help(self, cli_runner):
        """Test detect command help."""
        result = cli_runner.invoke(cli, ["detect", "--help"])
        assert result.exit_code == 0
        assert "Detect tables in PDF or image files" in result.output

    def test_detect_missing_file(self, cli_runner):
        """Test detect with non-existent file."""
        result = cli_runner.invoke(cli, ["detect", "nonexistent.pdf"])
        assert result.exit_code != 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_image(self, cli_runner, sample_image):
        """Test table detection in image."""
        result = cli_runner.invoke(cli, ["detect", str(sample_image)])

        assert result.exit_code == 0
        assert "Detecting tables in:" in result.output
        assert "Table Detection Results" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_pdf(self, cli_runner, sample_pdf):
        """Test table detection in PDF."""
        result = cli_runner.invoke(cli, ["detect", str(sample_pdf)])

        assert result.exit_code == 0
        assert "Detecting tables in:" in result.output
        assert "Table Detection Results" in result.output
        assert "Total tables found:" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_with_detector(self, cli_runner, sample_image):
        """Test detection with specific detector."""
        result = cli_runner.invoke(
            cli, ["detect", str(sample_image), "--detector", "tatr"]
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_pdf_summary(self, cli_runner, sample_pdf):
        """Test that PDF detection shows page-by-page summary."""
        result = cli_runner.invoke(cli, ["detect", str(sample_pdf)])

        assert result.exit_code == 0
        # Should show page information
        assert "Page" in result.output
        assert "Tables Found" in result.output
        assert "Table Dimensions" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_image_summary(self, cli_runner, sample_image):
        """Test that image detection shows table summary."""
        result = cli_runner.invoke(cli, ["detect", str(sample_image)])

        assert result.exit_code == 0
        # Should show table information
        assert "Table #" in result.output or "tables found" in result.output
        assert "Dimensions" in result.output or "No tables found" in result.output

    def test_detect_unsupported_format(self, cli_runner, temp_dir):
        """Test detection with unsupported file format."""
        unsupported_file = temp_dir / "test.txt"
        unsupported_file.write_text("Not an image or PDF")

        result = cli_runner.invoke(cli, ["detect", str(unsupported_file)])

        assert result.exit_code != 0
        assert "Unsupported file type" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_no_tables(self, cli_runner, temp_dir):
        """Test detection when no tables are found."""
        # Create an empty image
        from PIL import Image

        empty_image = temp_dir / "empty.png"
        img = Image.new("RGB", (100, 100), "white")
        img.save(empty_image)

        # Mock to return no tables
        from gmft_cli.discovery import registry

        class NoTablesDetector:
            def detect(self, image):
                return []

        original_create = registry.create_detector
        registry.create_detector = lambda name, config=None: NoTablesDetector()

        try:
            result = cli_runner.invoke(cli, ["detect", str(empty_image)])
            assert result.exit_code == 0
            assert "No tables found" in result.output
        finally:
            registry.create_detector = original_create

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detect_multipage_pdf(self, cli_runner, sample_pdf):
        """Test detection on multi-page PDF."""
        result = cli_runner.invoke(cli, ["detect", str(sample_pdf)])

        assert result.exit_code == 0
        # Should process multiple pages
        output_lines = result.output.split("\n")
        page_lines = [
            line
            for line in output_lines
            if "Page" in line or "│" in line and any(c.isdigit() for c in line)
        ]
        # Should have entries for multiple pages if PDF has multiple pages
        assert len(page_lines) >= 1
