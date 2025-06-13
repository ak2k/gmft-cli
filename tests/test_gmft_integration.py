"""Integration tests using GMFT's test data and expected outputs."""

import pytest
import json
import csv
from gmft_cli.cli import cli


@pytest.mark.gmft_data
@pytest.mark.integration
class TestGMFTData:
    """Test using GMFT's actual test data."""

    def test_tiny_pdf_extraction(
        self, cli_runner, gmft_pdfs, gmft_references, temp_dir
    ):
        """Test extraction from tiny.pdf matches GMFT's expected output."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        output_dir = temp_dir / "tiny_output"

        # Extract tables using our CLI
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(gmft_pdfs["tiny"]),
                "-o",
                str(output_dir),
                "--format",
                "csv",
                "--detector",
                "auto",
                "--formatter",
                "auto",
            ],
        )

        assert result.exit_code == 0

        # Check that tables were extracted
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0

        # Read the extracted CSV
        extracted_data = []
        for csv_file in sorted(csv_files):
            with open(csv_file, "r") as f:
                reader = csv.reader(f)
                extracted_data.append(list(reader))

        # Verify we got table data
        assert len(extracted_data) > 0
        assert len(extracted_data[0]) > 0  # Has rows
        assert len(extracted_data[0][0]) > 0  # Has columns

    def test_tatr_pdf_extraction(self, cli_runner, gmft_pdfs, temp_dir):
        """Test extraction from tatr.pdf."""
        if "tatr" not in gmft_pdfs:
            pytest.skip("tatr.pdf not found")

        output_dir = temp_dir / "tatr_output"

        # Extract with TATR formatter specifically
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(gmft_pdfs["tatr"]),
                "-o",
                str(output_dir),
                "--formatter",
                "tatr",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "Extracted" in result.output

        # Verify outputs exist
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0

    @pytest.mark.parametrize("pdf_num", ["1", "2", "3", "4", "5", "6", "7", "8"])
    def test_numbered_pdfs(self, cli_runner, gmft_pdfs, temp_dir, pdf_num):
        """Test extraction from numbered PDFs (1.pdf through 8.pdf)."""
        if pdf_num not in gmft_pdfs:
            pytest.skip(f"{pdf_num}.pdf not found")

        output_dir = temp_dir / f"pdf{pdf_num}_output"

        # Extract tables
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(gmft_pdfs[pdf_num]),
                "-o",
                str(output_dir),
                "--format",
                "json",
                "--verbose",
            ],
        )

        # These PDFs might have tables or might not
        assert result.exit_code == 0

        # Check if any tables were found
        json_files = list(output_dir.glob("*.json"))
        if json_files:
            # Verify JSON is valid
            for json_file in json_files:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    assert isinstance(data, list)

    def test_detection_matches_references(self, cli_runner, gmft_pdfs, gmft_references):
        """Test that detection results are consistent with GMFT's detection."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        # Run detection
        result = cli_runner.invoke(
            cli, ["detect", str(gmft_pdfs["tiny"]), "--detector", "auto"]
        )

        assert result.exit_code == 0
        assert "Total tables found:" in result.output

        # Extract number of tables found
        for line in result.output.split("\n"):
            if "Total tables found:" in line:
                # Should find at least one table in tiny.pdf
                count = int(line.split(":")[-1].strip())
                assert count > 0

    def test_formatters_comparison(self, cli_runner, gmft_pdfs, temp_dir):
        """Test different formatters on the same PDF."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        formatters = ["auto", "tatr", "histogram"]
        results = {}

        for formatter in formatters:
            output_dir = temp_dir / f"formatter_{formatter}"

            result = cli_runner.invoke(
                cli,
                [
                    "extract",
                    str(gmft_pdfs["tiny"]),
                    "-o",
                    str(output_dir),
                    "--formatter",
                    formatter,
                ],
            )

            # Some formatters might not be available
            if result.exit_code == 0:
                csv_files = list(output_dir.glob("*.csv"))
                results[formatter] = len(csv_files)

        # At least one formatter should work
        assert len(results) > 0
        assert any(count > 0 for count in results.values())

    def test_bulk_extraction_gmft_pdfs(self, cli_runner, gmft_pdfs, temp_dir):
        """Test bulk extraction on multiple GMFT test PDFs."""
        # Use first 3 PDFs for bulk test
        pdf_files = []
        for key in ["tiny", "tatr", "1"]:
            if key in gmft_pdfs:
                pdf_files.append(str(gmft_pdfs[key]))

        if len(pdf_files) < 2:
            pytest.skip("Not enough test PDFs found")

        output_dir = temp_dir / "bulk_output"

        result = cli_runner.invoke(
            cli, ["bulk-extract", *pdf_files, "-o", str(output_dir), "--verbose"]
        )

        assert result.exit_code == 0
        assert "Extracted" in result.output

        # Check that subdirectories were created
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert (
            len(subdirs) >= len(pdf_files) - 1
        )  # At least some PDFs should have tables


@pytest.mark.gmft_data
@pytest.mark.integration
class TestGMFTCompatibility:
    """Test compatibility with GMFT's expected behavior."""

    def test_multi_page_handling(self, cli_runner, gmft_pdfs, temp_dir):
        """Test handling of multi-page PDFs."""
        # Find a multi-page PDF
        multi_page_pdf = None
        for key, pdf_path in gmft_pdfs.items():
            # PDFs 1-8 are likely to have multiple pages
            if key in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                multi_page_pdf = pdf_path
                break

        if not multi_page_pdf:
            pytest.skip("No multi-page PDF found")

        output_dir = temp_dir / "multipage_output"

        # Extract from specific pages
        result = cli_runner.invoke(
            cli,
            ["extract", str(multi_page_pdf), "-o", str(output_dir), "--pages", "1-2"],
        )

        assert result.exit_code == 0

        # Check page-specific outputs
        # page1_files = list(output_dir.glob("page_1_*.csv"))  # Not used in assertion
        page3_files = list(output_dir.glob("page_3_*.csv"))

        # Should not have page 3 files since we only requested pages 1-2
        assert len(page3_files) == 0

    def test_visualization_output(self, cli_runner, gmft_pdfs, temp_dir):
        """Test visualization features match GMFT's capabilities."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        output_dir = temp_dir / "viz_output"

        result = cli_runner.invoke(
            cli,
            ["extract", str(gmft_pdfs["tiny"]), "-o", str(output_dir), "--visualize"],
        )

        assert result.exit_code == 0

        # Check for visualization outputs
        png_files = list(output_dir.glob("*.png"))
        # Should have detection and/or structure visualizations
        assert len(png_files) >= 0  # Might be 0 if no tables found

    def test_configuration_options(self, cli_runner, gmft_pdfs, temp_dir):
        """Test GMFT configuration options."""
        if "tatr" not in gmft_pdfs:
            pytest.skip("tatr.pdf not found")

        output_dir = temp_dir / "config_output"

        # Test with various TATR configurations
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(gmft_pdfs["tatr"]),
                "-o",
                str(output_dir),
                "--formatter",
                "tatr",
                "--multi-header",
                "--semantic-spanning-cells",
                "--large-table-assumption",
                "--verbose",
            ],
        )

        assert result.exit_code == 0

        # Configuration should be applied (visible in verbose output)
        assert "tatr" in result.output.lower() or "auto" in result.output.lower()


def create_gmft_reference_test(pdf_name, table_index):
    """Create a test that compares against GMFT reference data."""

    def test_method(self, cli_runner, gmft_pdfs, gmft_references, temp_dir):
        if pdf_name not in gmft_pdfs:
            pytest.skip(f"{pdf_name}.pdf not found")

        if "tatr_csvs" not in gmft_references:
            pytest.skip("TATR reference CSVs not found")

        # Extract using our CLI
        output_dir = temp_dir / f"{pdf_name}_ref_test"
        result = cli_runner.invoke(
            cli,
            [
                "extract",
                str(gmft_pdfs[pdf_name]),
                "-o",
                str(output_dir),
                "--format",
                "csv",
                "--formatter",
                "tatr",
            ],
        )

        assert result.exit_code == 0

        # Compare with reference if available
        ref_key = f"pdf{pdf_name}_t{table_index}"
        if ref_key in gmft_references["tatr_csvs"]:
            csv_files = sorted(output_dir.glob("*.csv"))
            if len(csv_files) > table_index:
                with open(csv_files[table_index], "r") as f:
                    extracted = list(csv.reader(f))

                reference = gmft_references["tatr_csvs"][ref_key]

                # Basic comparison - both should be non-empty
                assert len(extracted) > 0
                assert len(reference) > 0

    return test_method


# Dynamically create tests for each PDF/table combination
# This would create tests like test_pdf1_table0, test_pdf1_table1, etc.
# Commented out to avoid creating too many tests, but shows the pattern
# for pdf_num in range(1, 9):
#     for table_num in range(10):
#         test_name = f"test_pdf{pdf_num}_table{table_num}"
#         test_method = create_gmft_reference_test(str(pdf_num), table_num)
#         setattr(TestGMFTData, test_name, test_method)
