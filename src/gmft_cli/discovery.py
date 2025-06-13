"""Dynamic discovery of GMFT components."""

import importlib
import inspect
from typing import Dict, Type, Any, Optional, List, Tuple
from dataclasses import dataclass
import click


@dataclass
class ComponentInfo:
    """Information about a discovered component."""

    name: str
    class_type: Type
    module_path: str
    config_class: Optional[Type] = None
    description: Optional[str] = None
    aliases: List[str] = None


class ComponentRegistry:
    """Registry for dynamically discovered GMFT components."""

    def __init__(self):
        self._detectors: Dict[str, ComponentInfo] = {}
        self._formatters: Dict[str, ComponentInfo] = {}
        self._discovered = False

    def discover(self):
        """Discover all available components from gmft."""
        if self._discovered:
            return

        # Discover detectors
        self._discover_detectors()

        # Discover formatters
        self._discover_formatters()

        self._discovered = True

    def _discover_detectors(self):
        """Discover available detectors."""
        # First, try to discover from gmft.detectors module
        try:
            import gmft.detectors

            detector_modules = []

            # Try to list all submodules in gmft.detectors
            if hasattr(gmft.detectors, "__path__"):
                import pkgutil

                for importer, modname, ispkg in pkgutil.iter_modules(
                    gmft.detectors.__path__
                ):
                    if not ispkg:  # Only process modules, not subpackages
                        full_module_name = f"gmft.detectors.{modname}"
                        detector_modules.append(full_module_name)

            # Process each detector module
            for module_path in detector_modules:
                try:
                    module = importlib.import_module(module_path)
                    # Look for classes ending with 'Detector'
                    for attr_name in dir(module):
                        if attr_name.endswith("Detector") and not attr_name.startswith(
                            "_"
                        ):
                            detector_class = getattr(module, attr_name)
                            if inspect.isclass(detector_class):
                                # Look for corresponding config class
                                config_name = attr_name.replace("Detector", "Config")
                                config_class = getattr(module, config_name, None)
                                if not config_class:
                                    config_name = attr_name.replace(
                                        "Detector", "DetectorConfig"
                                    )
                                    config_class = getattr(module, config_name, None)

                                # Extract name from class name
                                name = (
                                    attr_name.replace("Detector", "")
                                    .replace("Table", "")
                                    .lower()
                                )

                                self._detectors[name] = ComponentInfo(
                                    name=name,
                                    class_type=detector_class,
                                    module_path=module_path,
                                    config_class=config_class,
                                    description=self._get_class_description(
                                        detector_class
                                    ),
                                    aliases=[attr_name],
                                )
                except ImportError:
                    continue
        except ImportError:
            pass

        # Also check gmft.auto for aliases
        try:
            auto_module = importlib.import_module("gmft.auto")
            if hasattr(auto_module, "AutoTableDetector"):
                self._detectors["auto"] = ComponentInfo(
                    name="auto",
                    class_type=auto_module.AutoTableDetector,
                    module_path="gmft.auto",
                    description="Automatic detector selection",
                    aliases=["AutoTableDetector"],
                )
        except ImportError:
            pass

    def _discover_formatters(self):
        """Discover available formatters."""
        # First, try to discover from gmft.formatters module
        try:
            import gmft.formatters

            formatter_modules = []

            # Try to list all submodules in gmft.formatters
            if hasattr(gmft.formatters, "__path__"):
                import pkgutil

                for importer, modname, ispkg in pkgutil.iter_modules(
                    gmft.formatters.__path__
                ):
                    if not ispkg:  # Only process modules, not subpackages
                        full_module_name = f"gmft.formatters.{modname}"
                        formatter_modules.append(full_module_name)

            # Process each formatter module
            for module_path in formatter_modules:
                try:
                    module = importlib.import_module(module_path)
                    # Look for classes ending with 'Formatter'
                    for attr_name in dir(module):
                        if attr_name.endswith("Formatter") and not attr_name.startswith(
                            "_"
                        ):
                            formatter_class = getattr(module, attr_name)
                            if inspect.isclass(formatter_class):
                                # Look for corresponding config class
                                config_class = None
                                for config_suffix in [
                                    "Config",
                                    "FormatConfig",
                                    "FormatterConfig",
                                ]:
                                    config_name = attr_name.replace(
                                        "Formatter", config_suffix
                                    )
                                    config_class = getattr(module, config_name, None)
                                    if config_class:
                                        break

                                # Extract name from class name
                                name = (
                                    attr_name.replace("Formatter", "")
                                    .replace("Table", "")
                                    .lower()
                                )

                                self._formatters[name] = ComponentInfo(
                                    name=name,
                                    class_type=formatter_class,
                                    module_path=module_path,
                                    config_class=config_class,
                                    description=self._get_class_description(
                                        formatter_class
                                    ),
                                    aliases=[attr_name],
                                )
                except ImportError:
                    continue
        except ImportError:
            pass

        # Also check gmft.auto for aliases
        try:
            auto_module = importlib.import_module("gmft.auto")
            if hasattr(auto_module, "AutoTableFormatter"):
                self._formatters["auto"] = ComponentInfo(
                    name="auto",
                    class_type=auto_module.AutoTableFormatter,
                    module_path="gmft.auto",
                    config_class=getattr(auto_module, "AutoFormatConfig", None),
                    description="Automatic formatter selection",
                    aliases=["AutoTableFormatter"],
                )
        except ImportError:
            pass

    def _get_class_description(self, cls: Type) -> Optional[str]:
        """Extract description from class docstring."""
        if cls.__doc__:
            # Get first line of docstring
            return cls.__doc__.strip().split("\n")[0]
        return None

    def get_detector(self, name: str) -> Optional[ComponentInfo]:
        """Get detector info by name."""
        self.discover()
        return self._detectors.get(name.lower())

    def get_formatter(self, name: str) -> Optional[ComponentInfo]:
        """Get formatter info by name."""
        self.discover()
        return self._formatters.get(name.lower())

    def list_detectors(self) -> List[str]:
        """List available detector names."""
        self.discover()
        return sorted(self._detectors.keys())

    def list_formatters(self) -> List[str]:
        """List available formatter names."""
        self.discover()
        return sorted(self._formatters.keys())

    def create_detector(self, name: str, config: Optional[Any] = None):
        """Create a detector instance."""
        info = self.get_detector(name)
        if not info:
            raise ValueError(f"Unknown detector: {name}")

        if config is not None:
            return info.class_type(config=config)
        return info.class_type()

    def create_formatter(self, name: str, config: Optional[Any] = None):
        """Create a formatter instance."""
        info = self.get_formatter(name)
        if not info:
            raise ValueError(f"Unknown formatter: {name}")

        if config is not None:
            return info.class_type(config=config)
        return info.class_type()

    def get_formatter_config_options(self, name: str) -> List[Tuple[str, Any, str]]:
        """Get configuration options for a formatter.

        Returns list of (option_name, default_value, description) tuples.
        """
        info = self.get_formatter(name)
        if not info or not info.config_class:
            return []

        options = []

        # Inspect config class for attributes
        if hasattr(info.config_class, "__dataclass_fields__"):
            # It's a dataclass
            for field_name, field in info.config_class.__dataclass_fields__.items():
                if field_name.startswith("_"):
                    continue

                default = (
                    field.default
                    if field.default is not field.default_factory
                    else None
                )
                field_type = field.type

                # Convert type to description
                type_desc = "value"
                if field_type is bool:
                    type_desc = "boolean"
                elif field_type is int:
                    type_desc = "integer"
                elif field_type is float:
                    type_desc = "float"
                elif field_type is str:
                    type_desc = "string"

                options.append((field_name, default, f"{field_name} ({type_desc})"))

        return options


# Global registry instance
registry = ComponentRegistry()


def get_detector_click_type():
    """Get Click choice type for detectors."""
    registry.discover()
    return click.Choice(registry.list_detectors(), case_sensitive=False)


def get_formatter_click_type():
    """Get Click choice type for formatters."""
    registry.discover()
    return click.Choice(registry.list_formatters(), case_sensitive=False)
