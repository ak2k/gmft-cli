"""Tests for component discovery functionality."""

import pytest
from gmft_cli.discovery import (
    ComponentRegistry,
    ComponentInfo,
    get_detector_click_type,
    get_formatter_click_type,
)


class TestComponentRegistry:
    """Test the component registry."""

    def test_registry_singleton(self):
        """Test that registry maintains discovered state."""
        registry = ComponentRegistry()
        registry.discover()
        assert registry._discovered is True

    def test_discover_detectors(self):
        """Test detector discovery."""
        registry = ComponentRegistry()
        registry._discover_detectors()

        # Should at least have 'auto' detector
        detectors = registry.list_detectors()
        assert "auto" in detectors

    def test_discover_formatters(self):
        """Test formatter discovery."""
        registry = ComponentRegistry()
        registry._discover_formatters()

        # Should at least have 'auto' formatter
        formatters = registry.list_formatters()
        assert "auto" in formatters

    def test_get_detector_info(self):
        """Test getting detector information."""
        registry = ComponentRegistry()
        registry.discover()

        auto_info = registry.get_detector("auto")
        assert auto_info is not None
        assert auto_info.name == "auto"
        assert auto_info.module_path is not None

    def test_get_formatter_info(self):
        """Test getting formatter information."""
        registry = ComponentRegistry()
        registry.discover()

        auto_info = registry.get_formatter("auto")
        assert auto_info is not None
        assert auto_info.name == "auto"
        assert auto_info.module_path is not None

    def test_case_insensitive_lookup(self):
        """Test that component lookup is case-insensitive."""
        registry = ComponentRegistry()
        registry.discover()

        assert registry.get_detector("AUTO") is not None
        assert registry.get_formatter("AUTO") is not None

    def test_unknown_component(self):
        """Test handling of unknown components."""
        registry = ComponentRegistry()
        registry.discover()

        assert registry.get_detector("nonexistent") is None
        assert registry.get_formatter("nonexistent") is None

    def test_create_detector(self):
        """Test creating detector instances."""
        registry = ComponentRegistry()
        registry.discover()

        if "auto" in registry.list_detectors():
            detector = registry.create_detector("auto")
            assert detector is not None

    def test_create_formatter(self):
        """Test creating formatter instances."""
        registry = ComponentRegistry()
        registry.discover()

        if "auto" in registry.list_formatters():
            formatter = registry.create_formatter("auto")
            assert formatter is not None

    def test_create_unknown_component_error(self):
        """Test error handling for unknown components."""
        registry = ComponentRegistry()
        registry.discover()

        with pytest.raises(ValueError, match="Unknown detector"):
            registry.create_detector("nonexistent")

        with pytest.raises(ValueError, match="Unknown formatter"):
            registry.create_formatter("nonexistent")

    def test_formatter_config_options(self):
        """Test getting formatter configuration options."""
        registry = ComponentRegistry()
        registry.discover()

        # Test with a formatter that has config
        if "auto" in registry.list_formatters():
            auto_info = registry.get_formatter("auto")
            if auto_info and auto_info.config_class:
                options = registry.get_formatter_config_options("auto")
                assert isinstance(options, list)

                # Each option should be a tuple of (name, default, description)
                for option in options:
                    assert len(option) == 3
                    assert isinstance(option[0], str)  # name
                    assert isinstance(option[2], str)  # description

    def test_click_types(self):
        """Test Click type generation for CLI options."""
        detector_type = get_detector_click_type()
        formatter_type = get_formatter_click_type()

        assert detector_type is not None
        assert formatter_type is not None

        # Should be Click Choice types
        assert hasattr(detector_type, "choices")
        assert hasattr(formatter_type, "choices")


class TestComponentInfo:
    """Test the ComponentInfo dataclass."""

    def test_component_info_creation(self):
        """Test creating ComponentInfo instances."""

        class DummyClass:
            """Dummy class for testing."""

            pass

        info = ComponentInfo(
            name="test",
            class_type=DummyClass,
            module_path="test.module",
            config_class=None,
            description="Test component",
            aliases=["TestComponent"],
        )

        assert info.name == "test"
        assert info.class_type == DummyClass
        assert info.module_path == "test.module"
        assert info.config_class is None
        assert info.description == "Test component"
        assert info.aliases == ["TestComponent"]


class TestDynamicDiscovery:
    """Test dynamic discovery features."""

    def test_class_description_extraction(self):
        """Test extracting descriptions from class docstrings."""
        registry = ComponentRegistry()

        class TestClass:
            """This is a test class.

            With multiple lines.
            """

            pass

        desc = registry._get_class_description(TestClass)
        assert desc == "This is a test class."

    def test_empty_docstring(self):
        """Test handling classes without docstrings."""
        registry = ComponentRegistry()

        class TestClass:
            pass

        desc = registry._get_class_description(TestClass)
        assert desc is None

    def test_real_gmft_discovery(self):
        """Test discovery with actual GMFT installation."""
        registry = ComponentRegistry()
        registry.discover()

        detectors = registry.list_detectors()
        formatters = registry.list_formatters()

        # Should discover standard GMFT components
        assert "tatr" in detectors or "auto" in detectors
        assert "tatr" in formatters or "auto" in formatters

        # Should be able to create instances
        if "auto" in detectors:
            detector = registry.create_detector("auto")
            assert detector is not None

        if "auto" in formatters:
            formatter = registry.create_formatter("auto")
            assert formatter is not None
