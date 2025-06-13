"""Tests for the bulk-extract command."""

import pytest
from pathlib import Path
from gmft_cli.cli import cli


class TestBulkExtractCommand:
    """Test the bulk-extract command functionality."""

    def test_bulk_extract_help(self, cli_runner):
        """Test bulk-extract command help."""
        result = cli_runner.invoke(cli, ["bulk-extract", "--help"])
        assert result.exit_code == 0
        assert "Extract tables from multiple PDF or image files" in result.output

    def test_bulk_extract_no_files(self, cli_runner):
        """Test bulk-extract with no files specified."""
        result = cli_runner.invoke(cli, ["bulk-extract"])
        assert result.exit_code != 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_multiple_files(self, cli_runner, multiple_pdfs, temp_dir):
        """Test bulk extraction with multiple files."""
        output_dir = temp_dir / "bulk_output"

        # Convert paths to strings
        file_args = [str(pdf) for pdf in multiple_pdfs]

        result = cli_runner.invoke(
            cli, ["bulk-extract", *file_args, "-o", str(output_dir)]
        )

        assert result.exit_code == 0
        assert output_dir.exists()

        # Should create subdirectories for each file
        for pdf in multiple_pdfs:
            file_output_dir = output_dir / pdf.stem
            assert file_output_dir.exists()

            # Should have extracted tables
            csv_files = list(file_output_dir.glob("*.csv"))
            assert len(csv_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_with_pattern(self, cli_runner, multiple_pdfs, temp_dir):
        """Test bulk extraction with glob pattern."""
        output_dir = temp_dir / "bulk_output"

        # Change to the directory containing PDFs
        import os

        original_cwd = os.getcwd()
        os.chdir(str(multiple_pdfs[0].parent))

        try:
            result = cli_runner.invoke(
                cli, ["bulk-extract", "--pattern", "*.pdf", "-o", str(output_dir)]
            )

            assert result.exit_code == 0
            assert output_dir.exists()

            # Should process all PDF files
            pdf_count = len(list(Path(".").glob("*.pdf")))
            subdirs = list(output_dir.iterdir())
            assert len(subdirs) == pdf_count
        finally:
            os.chdir(original_cwd)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_recursive(self, cli_runner, temp_dir):
        """Test bulk extraction with recursive search."""
        # Create nested directory structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        # Create PDFs in different directories
        import fitz

        for i, dir_path in enumerate([temp_dir, subdir]):
            pdf_path = dir_path / f"test_{i}.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text(fitz.Point(50, 50), f"Test {i}")
            doc.save(pdf_path)
            doc.close()

        output_dir = temp_dir / "bulk_output"

        # Change to temp_dir for pattern search
        import os

        original_cwd = os.getcwd()
        os.chdir(str(temp_dir))

        try:
            result = cli_runner.invoke(
                cli,
                [
                    "bulk-extract",
                    "--pattern",
                    "*.pdf",
                    "--recursive",
                    "-o",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0
            assert output_dir.exists()

            # Should find PDFs in both directories
            subdirs = list(output_dir.iterdir())
            assert len(subdirs) >= 2
        finally:
            os.chdir(original_cwd)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_with_format(self, cli_runner, multiple_pdfs, temp_dir):
        """Test bulk extraction with different output format."""
        output_dir = temp_dir / "bulk_output"
        file_args = [str(pdf) for pdf in multiple_pdfs]

        result = cli_runner.invoke(
            cli, ["bulk-extract", *file_args, "-o", str(output_dir), "--format", "json"]
        )

        assert result.exit_code == 0

        # Check for JSON files
        for pdf in multiple_pdfs:
            file_output_dir = output_dir / pdf.stem
            json_files = list(file_output_dir.glob("*.json"))
            assert len(json_files) > 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_with_detector_formatter(
        self, cli_runner, multiple_pdfs, temp_dir
    ):
        """Test bulk extraction with specific detector and formatter."""
        output_dir = temp_dir / "bulk_output"
        file_args = [str(pdf) for pdf in multiple_pdfs]

        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                *file_args,
                "-o",
                str(output_dir),
                "--detector",
                "tatr",
                "--formatter",
                "histogram",
            ],
        )

        assert result.exit_code == 0

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_verbose(self, cli_runner, multiple_pdfs, temp_dir):
        """Test bulk extraction with verbose output."""
        output_dir = temp_dir / "bulk_output"
        file_args = [
            str(pdf) for pdf in multiple_pdfs[:1]
        ]  # Just one file for cleaner output

        result = cli_runner.invoke(
            cli, ["bulk-extract", *file_args, "-o", str(output_dir), "--verbose"]
        )

        assert result.exit_code == 0
        assert "Processing:" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_keyword_filter(self, cli_runner, temp_dir):
        """Test bulk extraction with keyword filtering."""
        # Create PDFs with specific content
        import fitz

        # PDF with matching keyword
        pdf_with_keyword = temp_dir / "with_keyword.pdf"
        doc1 = fitz.open()
        page1 = doc1.new_page()
        page1.insert_text(fitz.Point(50, 50), "This contains a TABLE here")
        doc1.save(pdf_with_keyword)
        doc1.close()

        # PDF without keyword
        pdf_without_keyword = temp_dir / "without_keyword.pdf"
        doc2 = fitz.open()
        page2 = doc2.new_page()
        page2.insert_text(fitz.Point(50, 50), "This has no special words")
        doc2.save(pdf_without_keyword)
        doc2.close()

        output_dir = temp_dir / "bulk_output"

        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                str(pdf_with_keyword),
                str(pdf_without_keyword),
                "-o",
                str(output_dir),
                "--keyword-filter",
                "table",
                "--verbose",
            ],
        )

        assert result.exit_code == 0

        # Should only process the PDF with the keyword
        assert (output_dir / "with_keyword").exists()
        # The one without keyword might not have output or might be skipped

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_mixed_pattern_and_files(
        self, cli_runner, multiple_pdfs, temp_dir
    ):
        """Test bulk extraction with both pattern and explicit files."""
        output_dir = temp_dir / "bulk_output"

        # Create an additional PDF
        extra_pdf = temp_dir / "extra.pdf"
        import fitz

        doc = fitz.open()
        doc.new_page()
        doc.save(extra_pdf)
        doc.close()

        # Use first PDF explicitly and pattern for others
        import os

        original_cwd = os.getcwd()
        os.chdir(str(temp_dir))

        try:
            result = cli_runner.invoke(
                cli,
                [
                    "bulk-extract",
                    str(multiple_pdfs[0]),
                    "--pattern",
                    "document_*.pdf",
                    "-o",
                    str(output_dir),
                ],
            )

            assert result.exit_code == 0

            # Should process both explicit file and pattern matches
            subdirs = list(output_dir.iterdir())
            assert len(subdirs) >= len(multiple_pdfs)
        finally:
            os.chdir(original_cwd)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_default_output_dir(self, cli_runner, multiple_pdfs):
        """Test bulk extraction with default output directory."""
        file_args = [str(pdf) for pdf in multiple_pdfs[:1]]

        result = cli_runner.invoke(cli, ["bulk-extract", *file_args])

        assert result.exit_code == 0

        # Should create default directory
        default_dir = Path("bulk_extracted_tables")
        assert default_dir.exists()

        # Cleanup
        import shutil

        shutil.rmtree(default_dir)

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_bulk_extract_error_handling(self, cli_runner, temp_dir):
        """Test bulk extraction error handling."""
        # Create one valid PDF and one invalid file
        valid_pdf = temp_dir / "valid.pdf"
        import fitz

        doc = fitz.open()
        doc.new_page()
        doc.save(valid_pdf)
        doc.close()

        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("Not a PDF")

        output_dir = temp_dir / "bulk_output"

        result = cli_runner.invoke(
            cli,
            [
                "bulk-extract",
                str(valid_pdf),
                str(invalid_file),
                "-o",
                str(output_dir),
                "--verbose",
            ],
        )

        # Should complete even with errors
        assert result.exit_code == 0
        assert "Error processing" in result.output

        # Should still process valid file
        assert (output_dir / "valid").exists()

    def test_bulk_extract_no_files_found(self, cli_runner, temp_dir):
        """Test bulk extraction when no files match pattern."""
        import os

        original_cwd = os.getcwd()
        os.chdir(str(temp_dir))

        try:
            result = cli_runner.invoke(
                cli, ["bulk-extract", "--pattern", "*.nonexistent"]
            )

            assert result.exit_code == 0
            assert "No files found to process" in result.output
        finally:
            os.chdir(original_cwd)
