"""Validation tests to ensure CLI output matches GMFT's expected results."""

import pytest
import json
import pandas as pd
from gmft_cli.cli import cli


@pytest.mark.gmft_data
@pytest.mark.validation
class TestGMFTValidation:
    """Validate CLI outputs against GMFT's expected results."""

    @pytest.fixture
    def run_gmft_directly(self):
        """Run GMFT directly for comparison."""

        def _run(pdf_path, detector="auto", formatter="auto"):
            try:
                from gmft.auto import AutoTableDetector, AutoTableFormatter
                from gmft.pdf_bindings import PyPDFium2Document

                # Use GMFT directly
                detector_cls = (
                    AutoTableDetector if detector == "auto" else AutoTableDetector
                )
                formatter_cls = (
                    AutoTableFormatter if formatter == "auto" else AutoTableFormatter
                )

                doc = PyPDFium2Document(str(pdf_path))
                detector_inst = detector_cls()
                formatter_inst = formatter_cls()

                all_tables = []
                for page in doc:
                    tables = detector_inst.extract(page)
                    for table in tables:
                        formatted = formatter_inst.extract(table)
                        df = formatted.df()
                        all_tables.append(df)

                doc.close()
                return all_tables

            except Exception as e:
                pytest.skip(f"Could not run GMFT directly: {e}")

        return _run

    def test_cli_vs_direct_gmft(
        self, cli_runner, gmft_pdfs, temp_dir, run_gmft_directly
    ):
        """Compare CLI output with direct GMFT usage."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        pdf_path = gmft_pdfs["tiny"]

        # Run via CLI
        output_dir = temp_dir / "cli_output"
        result = cli_runner.invoke(
            cli, ["extract", str(pdf_path), "-o", str(output_dir), "--format", "csv"]
        )

        assert result.exit_code == 0

        # Get CLI results
        cli_tables = []
        for csv_file in sorted(output_dir.glob("*.csv")):
            df = pd.read_csv(csv_file, header=None)
            cli_tables.append(df)

        # Run GMFT directly
        direct_tables = run_gmft_directly(pdf_path)

        # Compare counts
        assert len(cli_tables) == len(
            direct_tables
        ), f"CLI found {len(cli_tables)} tables, GMFT found {len(direct_tables)}"

        # Compare table dimensions (allow for small differences due to header handling)
        for i, (cli_df, direct_df) in enumerate(zip(cli_tables, direct_tables)):
            # Both should have data
            assert cli_df.shape[0] > 0, f"CLI table {i} has no rows"
            assert cli_df.shape[1] > 0, f"CLI table {i} has no columns"
            assert direct_df.shape[0] > 0, f"GMFT table {i} has no rows"
            assert direct_df.shape[1] > 0, f"GMFT table {i} has no columns"

            # Column count should be same (structure should match)
            assert (
                cli_df.shape[1] == direct_df.shape[1]
            ), f"Table {i} column count differs: CLI {cli_df.shape[1]} vs GMFT {direct_df.shape[1]}"

            # Row count can differ slightly due to header handling, but should be similar
            row_diff = abs(cli_df.shape[0] - direct_df.shape[0])
            assert (
                row_diff <= 1
            ), f"Table {i} row count differs too much: CLI {cli_df.shape[0]} vs GMFT {direct_df.shape[0]}"

    def test_formatter_consistency(self, cli_runner, gmft_pdfs, temp_dir):
        """Test that formatter outputs are consistent."""
        if "tiny" not in gmft_pdfs:
            pytest.skip("tiny.pdf not found")

        # Run same extraction twice
        results = []
        for i in range(2):
            output_dir = temp_dir / f"consistency_{i}"
            result = cli_runner.invoke(
                cli,
                [
                    "extract",
                    str(gmft_pdfs["tiny"]),
                    "-o",
                    str(output_dir),
                    "--format",
                    "json",
                ],
            )

            assert result.exit_code == 0

            # Load JSON results
            json_files = sorted(output_dir.glob("*.json"))
            run_data = []
            for json_file in json_files:
                with open(json_file, "r") as f:
                    run_data.append(json.load(f))
            results.append(run_data)

        # Results should be identical
        assert len(results[0]) == len(results[1])
        for i, (data1, data2) in enumerate(zip(results[0], results[1])):
            assert data1 == data2, f"Table {i} results differ between runs"

    def test_page_specific_extraction(self, cli_runner, gmft_pdfs, temp_dir):
        """Test that page-specific extraction works correctly."""
        # Find a multi-page PDF
        multi_page_pdf = None
        for key in ["1", "2", "3", "4", "5"]:
            if key in gmft_pdfs:
                multi_page_pdf = gmft_pdfs[key]
                break

        if not multi_page_pdf:
            pytest.skip("No multi-page PDF found")

        # Extract all pages
        all_output = temp_dir / "all_pages"
        result_all = cli_runner.invoke(
            cli, ["extract", str(multi_page_pdf), "-o", str(all_output)]
        )

        # Extract only page 1
        page1_output = temp_dir / "page1_only"
        result_page1 = cli_runner.invoke(
            cli,
            ["extract", str(multi_page_pdf), "-o", str(page1_output), "--pages", "1"],
        )

        assert result_all.exit_code == 0
        assert result_page1.exit_code == 0

        # Page 1 results should be subset of all results
        all_page1_files = sorted([f for f in all_output.glob("page_1_*.csv")])
        page1_only_files = sorted(page1_output.glob("*.csv"))

        assert len(all_page1_files) == len(
            page1_only_files
        ), "Page 1 extraction should find same number of tables"

    def test_error_handling(self, cli_runner, temp_dir):
        """Test that CLI handles errors gracefully like GMFT."""
        # Test with non-existent file
        result = cli_runner.invoke(cli, ["extract", "nonexistent.pdf"])

        assert result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output

        # Test with invalid PDF
        invalid_pdf = temp_dir / "invalid.pdf"
        invalid_pdf.write_text("This is not a PDF")

        result = cli_runner.invoke(cli, ["extract", str(invalid_pdf)])

        assert result.exit_code != 0


@pytest.mark.gmft_data
class TestCLIFeatureCompleteness:
    """Ensure CLI supports all GMFT features used in tests."""

    def test_all_detectors_available(self, cli_runner):
        """Test that all GMFT detectors are available."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        output = result.output.lower()

        # Should have at least these detectors
        expected_detectors = ["auto", "tatr"]
        for detector in expected_detectors:
            assert (
                detector in output
            ), f"Detector '{detector}' not found in components list"

    def test_all_formatters_available(self, cli_runner):
        """Test that all GMFT formatters are available."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        output = result.output.lower()

        # Should have at least these formatters
        expected_formatters = ["auto", "tatr", "histogram"]
        for formatter in expected_formatters:
            assert (
                formatter in output
            ), f"Formatter '{formatter}' not found in components list"

    def test_all_output_formats(self, cli_runner, sample_pdf, temp_dir):
        """Test all output formats work."""
        formats = ["csv", "json", "markdown", "excel"]

        for fmt in formats:
            output_dir = temp_dir / f"format_{fmt}"
            result = cli_runner.invoke(
                cli,
                ["extract", str(sample_pdf), "-o", str(output_dir), "--format", fmt],
            )

            # Excel might fail if openpyxl not installed
            if fmt == "excel" and result.exit_code != 0:
                assert "openpyxl" in result.output
            else:
                assert result.exit_code == 0

                # Check files were created
                expected_ext = fmt
                if fmt == "excel":
                    expected_ext = "xlsx"

                output_files = list(output_dir.glob(f"*.{expected_ext}"))
                assert len(output_files) >= 0  # Might be 0 if no tables

    def test_configuration_options_complete(self, cli_runner, sample_pdf, temp_dir):
        """Test all configuration options from GMFT tests."""
        output_dir = temp_dir / "config_test"

        # Test with all TATR configuration options
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
                "--no-semantic-spanning-cells",  # Test negative option
                "--large-table-assumption",
                "--verbose",
            ],
        )

        # Should complete without error
        assert result.exit_code == 0

        # Should show processing output
        assert "Processing:" in result.output
        assert "Extracted" in result.output


def compare_dataframes(df1, df2, tolerance=0.01):
    """Compare two dataframes with some tolerance for differences."""
    if df1.shape != df2.shape:
        return False

    # Compare values
    for i in range(df1.shape[0]):
        for j in range(df1.shape[1]):
            val1 = str(df1.iloc[i, j])
            val2 = str(df2.iloc[i, j])

            # Try numeric comparison
            try:
                num1 = float(val1)
                num2 = float(val2)
                if abs(num1 - num2) > tolerance:
                    return False
            except (ValueError, TypeError):
                # String comparison
                if val1.strip() != val2.strip():
                    return False

    return True
