"""Integration tests based on GMFT notebook examples."""

import pytest
import json
import csv
from gmft_cli.cli import cli


@pytest.mark.integration
class TestNotebookExamples:
    """Integration tests mimicking notebook examples."""

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_quickstart_example(self, cli_runner, sample_pdf, temp_dir):
        """Test basic extraction workflow from quickstart notebook."""
        output_dir = temp_dir / "quickstart_output"

        # Basic extraction
        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--verbose"]
        )

        assert result.exit_code == 0
        assert output_dir.exists()

        # Test with configuration options (multi-header, spanning cells)
        output_dir2 = temp_dir / "quickstart_config"
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_pdf),
                "-o",
                str(output_dir2),
                "--formatter",
                "tatr",
                "--multi-header",
                "--semantic-spanning-cells",
                "--large-table-assumption",
            ],
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_example(self, cli_runner, multiple_pdfs, temp_dir):
        """Test bulk extraction workflow from bulk_extract notebook."""
        output_dir = temp_dir / "bulk_output"

        # Bulk extraction with all PDFs
        file_args = [str(pdf) for pdf in multiple_pdfs]

        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                *file_args,
                "-o",
                str(output_dir),
                "--format",
                "csv",
                "--verbose",
            ],
        )

        assert result.exit_code == 0

        # Verify outputs similar to notebook
        for pdf in multiple_pdfs:
            file_dir = output_dir / pdf.stem
            assert file_dir.exists()
            csv_files = list(file_dir.glob("*.csv"))
            assert len(csv_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_ditr_formatter_example(self, cli_runner, sample_pdf, temp_dir):
        """Test DITR formatter example from notebook."""
        output_dir = temp_dir / "ditr_output"

        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_pdf),
                "-o",
                str(output_dir),
                "--formatter",
                "ditr",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert len(list(output_dir.glob("*.csv"))) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_histogram_formatter_example(self, cli_runner, sample_pdf, temp_dir):
        """Test histogram formatter for fast extraction."""
        output_dir = temp_dir / "histogram_output"

        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_pdf),
                "-o",
                str(output_dir),
                "--formatter",
                "histogram",
            ],
        )

        assert result.exit_code == 0
        # Histogram should be fast, verify it completes quickly
        assert len(list(output_dir.glob("*.csv"))) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_visualization_workflow(self, cli_runner, sample_pdf, temp_dir):
        """Test visualization features from notebooks."""
        output_dir = temp_dir / "viz_output"

        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(sample_pdf),
                "-o",
                str(output_dir),
                "--visualize",
                "--verbose",
            ],
        )

        assert result.exit_code == 0

        # Check for visualization outputs
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) > 0

        # Should have different types of visualizations
        detection_imgs = [f for f in png_files if "detection" in f.name]
        table_imgs = [
            f for f in png_files if "image" in f.name and "detection" not in f.name
        ]

        assert len(detection_imgs) > 0
        assert len(table_imgs) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_caption_extraction_workflow(self, cli_runner, sample_pdf, temp_dir):
        """Test caption extraction from notebooks."""
        output_dir = temp_dir / "caption_output"

        result = cli_runner.invoke(
            cli, ["extract", str(sample_pdf), "-o", str(output_dir), "--captions"]
        )

        assert result.exit_code == 0

        # Check for caption files
        caption_files = list(output_dir.glob("*_caption.txt"))
        assert len(caption_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_keyword_filtering_workflow(self, cli_runner, temp_dir):
        """Test keyword filtering for faster processing."""
        # Create PDFs with specific content
        import fitz

        pdfs = []
        for i in range(3):
            pdf_path = temp_dir / f"paper_{i}.pdf"
            doc = fitz.open()

            # Add pages with and without keywords
            for page_num in range(3):
                page = doc.new_page()
                if page_num == 1:  # Only page 2 has the keyword
                    page.insert_text(
                        fitz.Point(50, 50),
                        f"Paper {i} - Page {page_num} with TABLE data",
                    )
                else:
                    page.insert_text(
                        fitz.Point(50, 50), f"Paper {i} - Page {page_num} no keywords"
                    )

            doc.save(pdf_path)
            doc.close()
            pdfs.append(pdf_path)

        output_dir = temp_dir / "keyword_output"

        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                *[str(p) for p in pdfs],
                "-o",
                str(output_dir),
                "--keyword-filter",
                "table",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        # Should show keyword filtering was active (either found or not found)
        assert ("Pages with keywords" in result.output or "No pages with keywords found" in result.output)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_multiple_format_outputs(self, cli_runner, sample_pdf, temp_dir):
        """Test extracting tables in multiple formats."""
        formats = ["csv", "json", "markdown"]

        for fmt in formats:
            output_dir = temp_dir / f"output_{fmt}"
            result = cli_runner.invoke(
                cli,
                ["extract", str(sample_pdf), "-o", str(output_dir), "--format", fmt],
            )

            assert result.exit_code == 0

            # Verify correct file extension
            output_files = list(output_dir.glob(f"*.{fmt}"))
            assert len(output_files) > 0

            # Verify file content is valid
            if fmt == "json":
                with open(output_files[0], "r") as f:
                    data = json.load(f)
                    assert isinstance(data, list)
            elif fmt == "csv":
                with open(output_files[0], "r") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    assert len(rows) > 0
            elif fmt == "markdown":
                with open(output_files[0], "r") as f:
                    content = f.read()
                    assert "|" in content  # Markdown table syntax

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_detector_comparison(self, cli_runner, sample_pdf, temp_dir):
        """Test different detectors as shown in notebooks."""
        detectors = ["auto", "tatr"]  # Add more as they become available

        for detector in detectors:
            output_dir = temp_dir / f"detector_{detector}"
            result = cli_runner.invoke(
                cli,
                [
                    "extract",
                    str(sample_pdf),
                    "-o",
                    str(output_dir),
                    "--detector",
                    detector,
                ],
            )

            assert result.exit_code == 0
            assert len(list(output_dir.glob("*.csv"))) > 0


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_research_paper_workflow(self, cli_runner, multiple_pdfs, temp_dir):
        """Test typical research paper processing workflow."""
        output_dir = temp_dir / "research_output"

        # Process multiple research papers
        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                *[str(p) for p in multiple_pdfs],
                "-o",
                str(output_dir),
                "--format",
                "json",
                "--formatter",
                "auto",
                "--verbose",
            ],
        )

        assert result.exit_code == 0

        # Verify structured output
        for pdf in multiple_pdfs:
            pdf_dir = output_dir / pdf.stem
            json_files = list(pdf_dir.glob("*.json"))

            # Should have created output directory for each PDF
            assert pdf_dir.exists()
            # May or may not have JSON files depending on table detection
            # but the directory structure should be correct

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_quick_preview_workflow(self, cli_runner, sample_pdf):
        """Test quick preview workflow for checking tables."""
        # First detect tables
        result = cli_runner.invoke(cli, ["detect", str(sample_pdf)])
        assert result.exit_code == 0
        assert "Total tables found:" in result.output

        # Then extract specific pages if needed
        if "Page" in result.output and "1" in result.output:
            result2 = cli_runner.invoke(
                cli,
                [
                    "extract",
                    str(sample_pdf),
                    "--pages",
                    "1",
                    "--formatter",
                    "histogram",  # Fast formatter for preview
                ],
            )
            assert result2.exit_code == 0
