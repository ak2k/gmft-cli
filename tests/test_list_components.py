"""Tests for the list-components command."""

import pytest
from gmft_cli.cli import cli


class TestListComponentsCommand:
    """Test the list-components command functionality."""

    def test_list_components_help(self, cli_runner):
        """Test list-components command help."""
        result = cli_runner.invoke(cli, ["list-components", "--help"])
        assert result.exit_code == 0
        assert "List all available detectors and formatters" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_list_components_output(self, cli_runner):
        """Test list-components shows detectors and formatters."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        assert "Available Detectors" in result.output
        assert "Available Formatters" in result.output
        assert "Formatter Configuration Options" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_list_components_shows_modules(self, cli_runner):
        """Test that list-components shows module paths."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        # Should show module paths
        assert "mock.detectors" in result.output or "gmft.detectors" in result.output
        assert "mock.formatters" in result.output or "gmft.formatters" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_list_components_shows_config_support(self, cli_runner):
        """Test that list-components shows which formatters have config."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        # Should show config support indicators
        assert "Has Config" in result.output
        assert "✓" in result.output or "✗" in result.output

    @pytest.mark.usefixtures("mock_gmft_components")
    def test_list_components_shows_descriptions(self, cli_runner):
        """Test that list-components shows component descriptions."""
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        # Should show descriptions
        assert "Description" in result.output
        assert (
            "Mock detector for testing" in result.output
            or "No description available" in result.output
        )

    def test_list_components_with_real_gmft(self, cli_runner):
        """Test list-components with actual GMFT if available."""
        # This test will use real GMFT components if installed
        result = cli_runner.invoke(cli, ["list-components"])

        assert result.exit_code == 0
        # Basic structure should always be present
        assert "Available Detectors" in result.output
        assert "Available Formatters" in result.output
