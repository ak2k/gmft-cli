"""Tests for the extract command."""

import pytest
import csv
import json
from gmft_cli.cli import cli


class TestExtractCommand:
    """Test the extract command functionality."""

    def test_extract_help(self, cli_runner):
        """Test extract command help."""
        result = cli_runner.invoke(cli, ["extract", "--help"])
        assert result.exit_code == 0
        assert "Extract tables from PDF or image files" in result.output

    def test_extract_missing_file(self, cli_runner):
        """Test extract with non-existent file."""
        result = cli_runner.invoke(cli, ["extract", "nonexistent.pdf"])
        assert result.exit_code != 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_image_default(self, cli_runner, sample_image, temp_dir):
        """Test basic image extraction with default settings."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_image), "-o", str(output_dir)]
        )

        assert result.exit_code == 0
        assert output_dir.exists()

        # Check for extracted CSV files
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_pdf_default(self, cli_runner, sample_pdf, temp_dir):
        """Test basic PDF extraction with default settings."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir)]
        )

        assert result.exit_code == 0
        assert output_dir.exists()

        # Check for extracted files
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_json_format(self, cli_runner, sample_image, temp_dir):
        """Test extraction with JSON output format."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            ["extract", str(sample_image), "-o", str(output_dir), "--format", "json"],
        )

        assert result.exit_code == 0

        # Check for JSON files
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) > 0

        # Verify JSON is valid
        with open(json_files[0], "r") as f:
            data = json.load(f)
            assert isinstance(data, list)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_markdown_format(self, cli_runner, sample_image, temp_dir):
        """Test extraction with Markdown output format."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_image),
                "-o",
                str(output_dir),
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0

        # Check for Markdown files
        md_files = list(output_dir.glob("*.markdown"))
        assert len(md_files) > 0

        # Verify Markdown contains table syntax
        with open(md_files[0], "r") as f:
            content = f.read()
            assert "|" in content  # Markdown table syntax

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_excel_format(self, cli_runner, sample_image, temp_dir):
        """Test extraction with Excel output format."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            ["extract", str(sample_image), "-o", str(output_dir), "--format", "excel"],
        )

        assert result.exit_code == 0

        # Check for Excel files
        excel_files = list(output_dir.glob("*.excel"))
        assert len(excel_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_with_pages(self, cli_runner, sample_pdf, temp_dir):
        """Test extraction with specific page selection."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--pages", "1"]
        )

        assert result.exit_code == 0

        # Should only extract from page 1
        csv_files = list(output_dir.glob("page_1_*.csv"))
        assert len(csv_files) > 0

        # Should not have page 2 files
        page2_files = list(output_dir.glob("page_2_*.csv"))
        assert len(page2_files) == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_with_page_range(self, cli_runner, sample_pdf, temp_dir):
        """Test extraction with page range."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--pages", "1-2"]
        )

        assert result.exit_code == 0
        assert output_dir.exists()

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_verbose(self, cli_runner, sample_image, temp_dir):
        """Test extraction with verbose output."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_image), "-o", str(output_dir), "--verbose"]
        )

        assert result.exit_code == 0
        # Verbose output should contain more information
        assert len(result.output) > 100

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_different_detector(self, cli_runner, sample_image, temp_dir):
        """Test extraction with different detector."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            ["extract", str(sample_image), "-o", str(output_dir), "--detector", "tatr"],
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_different_formatter(self, cli_runner, sample_image, temp_dir):
        """Test extraction with different formatter."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_image),
                "-o",
                str(output_dir),
                "--formatter",
                "histogram",
            ],
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_with_config_options(self, cli_runner, sample_pdf, temp_dir):
        """Test extraction with formatter configuration options."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_pdf),
                "-o",
                str(output_dir),
                "--formatter",
                "tatr",
                "--multi-header",
                "--semantic-spanning-cells",
                "--large-table-assumption",
            ],
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_with_visualization(self, cli_runner, sample_image, temp_dir):
        """Test extraction with visualization enabled."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_image), "-o", str(output_dir), "--visualize"]
        )

        assert result.exit_code == 0

        # Should create visualization images
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) > 0

        # Check for different visualization types
        detection_files = [f for f in png_files if "detection" in f.name]
        image_files = [
            f for f in png_files if "image" in f.name and "detection" not in f.name
        ]

        assert len(detection_files) > 0
        assert len(image_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_with_captions(self, cli_runner, sample_pdf, temp_dir):
        """Test extraction with caption extraction enabled."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--captions"]
        )

        assert result.exit_code == 0

        # Should create caption files
        caption_files = list(output_dir.glob("*_caption.txt"))
        assert len(caption_files) > 0

        # Verify caption content
        with open(caption_files[0], "r") as f:
            caption = f.read()
            assert len(caption) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_default_output_dir(self, cli_runner, sample_image):
        """Test extraction with default output directory."""
        result = cli_runner.invoke(cli, ["extract", str(sample_image)])

        assert result.exit_code == 0

        # Should create default output directory
        expected_dir = sample_image.parent / f"{sample_image.stem}_tables"
        assert expected_dir.exists()

        # Cleanup
        import shutil

        shutil.rmtree(expected_dir)

    def test_extract_unsupported_format(self, cli_runner, temp_dir):
        """Test extraction with unsupported file format."""
        unsupported_file = temp_dir / "test.txt"
        unsupported_file.write_text("Not an image or PDF")

        result = cli_runner.invoke(cli, ["extract", str(unsupported_file)])

        assert result.exit_code != 0
        assert "Unsupported file type" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_extract_output_structure(self, cli_runner, sample_pdf, temp_dir):
        """Test the structure of extracted output."""
        output_dir = temp_dir / "output"
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--format", "csv"]
        )

        assert result.exit_code == 0

        # Check file naming convention
        csv_files = list(output_dir.glob("*.csv"))
        assert all("page_" in f.name and "_table_" in f.name for f in csv_files)

        # Verify CSV content structure
        if csv_files:
            with open(csv_files[0], "r") as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) > 0  # Should have content
                assert len(rows[0]) > 0  # Should have columns
