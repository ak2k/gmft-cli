"""Pytest configuration and fixtures for GMFT CLI tests."""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from click.testing import CliRunner
from PIL import Image, ImageDraw, ImageFont


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample image with a simple table."""
    img_path = temp_dir / "sample_table.png"

    # Create a simple table image
    width, height = 600, 400
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Draw table grid
    rows, cols = 4, 3
    cell_width = width // cols
    cell_height = height // rows

    # Draw horizontal lines
    for i in range(rows + 1):
        y = i * cell_height
        draw.line([(0, y), (width, y)], fill="black", width=2)

    # Draw vertical lines
    for i in range(cols + 1):
        x = i * cell_width
        draw.line([(x, 0), (x, height)], fill="black", width=2)

    # Add some text to cells
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    table_data = [
        ["Header 1", "Header 2", "Header 3"],
        ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
        ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"],
        ["Row 3 Col 1", "Row 3 Col 2", "Row 3 Col 3"],
    ]

    for row_idx, row in enumerate(table_data):
        for col_idx, text in enumerate(row):
            x = col_idx * cell_width + 10
            y = row_idx * cell_height + 10
            draw.text((x, y), text, fill="black", font=font)

    img.save(img_path)
    return img_path


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF with tables using available backend."""
    pdf_path = temp_dir / "sample_tables.pdf"

    # Try PyMuPDF first
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page()

        # Add a simple table
        rect = fitz.Rect(50, 50, 550, 300)

        # Draw table borders
        rows, cols = 4, 3
        cell_width = (rect.x1 - rect.x0) / cols
        cell_height = (rect.y1 - rect.y0) / rows

        # Draw horizontal lines
        for i in range(rows + 1):
            y = rect.y0 + i * cell_height
            page.draw_line(fitz.Point(rect.x0, y), fitz.Point(rect.x1, y))

        # Draw vertical lines
        for i in range(cols + 1):
            x = rect.x0 + i * cell_width
            page.draw_line(fitz.Point(x, rect.y0), fitz.Point(x, rect.y1))

        # Add text to cells
        table_data = [
            ["Product", "Price", "Quantity"],
            ["Apple", "$1.00", "10"],
            ["Banana", "$0.50", "20"],
            ["Orange", "$0.75", "15"],
        ]

        for row_idx, row in enumerate(table_data):
            for col_idx, text in enumerate(row):
                x = rect.x0 + col_idx * cell_width + 5
                y = rect.y0 + row_idx * cell_height + 15
                page.insert_text(fitz.Point(x, y), text, fontsize=11)

        # Add caption
        page.insert_text(fitz.Point(50, 320), "Table 1: Product Inventory", fontsize=12)

        # Add a second page
        page2 = doc.new_page()
        page2.insert_text(fitz.Point(50, 50), "Page 2 - Another table", fontsize=14)

        doc.save(pdf_path)
        doc.close()
        return pdf_path

    except ImportError:
        pass

    # Try pypdfium2 as fallback
    try:
        import pypdfium2  # noqa: F401 - used for PDF generation capability check
        from PIL import Image, ImageDraw

        # Create images for PDF pages
        img1 = Image.new("RGB", (612, 792), "white")
        draw1 = ImageDraw.Draw(img1)

        # Draw a simple table
        table_x, table_y = 50, 50
        cell_width, cell_height = 100, 50
        rows, cols = 4, 3

        for i in range(rows + 1):
            y = table_y + i * cell_height
            draw1.line(
                [(table_x, y), (table_x + cols * cell_width, y)], fill="black", width=2
            )

        for i in range(cols + 1):
            x = table_x + i * cell_width
            draw1.line(
                [(x, table_y), (x, table_y + rows * cell_height)], fill="black", width=2
            )

        # Save as PDF using pypdfium2
        # Note: This is a simplified approach - in production you'd use proper PDF generation
        img1.save(pdf_path.with_suffix(".png"))

        # For testing, we'll create a minimal PDF
        # If pypdfium2 doesn't support direct PDF creation, fall back to a mock
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")  # Minimal valid PDF
        return pdf_path

    except ImportError:
        pass

    # If no PDF library available, create a mock PDF for testing
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")  # Minimal valid PDF
    return pdf_path


@pytest.fixture
def multiple_pdfs(temp_dir):
    """Create multiple PDFs for bulk testing."""
    pdf_paths = []

    # Try to use available PDF backend
    try:
        import fitz

        for i in range(3):
            pdf_path = temp_dir / f"document_{i+1}.pdf"
            doc = fitz.open()
            page = doc.new_page()

            # Add a simple table with different data
            rect = fitz.Rect(50, 50, 350, 200)

            # Draw a 3x3 grid
            for j in range(4):
                y = rect.y0 + j * 50
                page.draw_line(fitz.Point(rect.x0, y), fitz.Point(rect.x1, y))
                x = rect.x0 + j * 100
                if j < 4:
                    page.draw_line(fitz.Point(x, rect.y0), fitz.Point(x, rect.y1))

            # Add some text
            page.insert_text(fitz.Point(60, 80), f"Doc {i+1} Table", fontsize=12)

            doc.save(pdf_path)
            doc.close()
            pdf_paths.append(pdf_path)

    except ImportError:
        # Fallback: create minimal PDFs
        for i in range(3):
            pdf_path = temp_dir / f"document_{i+1}.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            pdf_paths.append(pdf_path)

    return pdf_paths


@pytest.fixture
def mock_gmft_components(monkeypatch):
    """Mock GMFT components for testing without actual GMFT installation."""

    class MockDetector:
        def __init__(self, config=None):
            self.config = config

        def detect(self, image):
            # Return mock detected tables as table objects (for both detect and extract commands)
            return [MockTable()]

        def extract(self, page):
            # Return mock detected tables for PDF pages
            return [MockTable()]

    class MockFormatter:
        def __init__(self, config=None):
            self.config = config

        def format(self, table):
            # Return mock formatted data
            return [
                ["Header 1", "Header 2", "Header 3"],
                ["Data 1", "Data 2", "Data 3"],
                ["Data 4", "Data 5", "Data 6"],
            ]

        def extract(self, table):
            # Return mock formatted table (should return a formatted table object)
            class MockFormattedTable:
                def __init__(self):
                    self.data = [
                        ["Header 1", "Header 2", "Header 3"],
                        ["Data 1", "Data 2", "Data 3"],
                        ["Data 4", "Data 5", "Data 6"],
                    ]

                def visualize(self, return_img=False, **kwargs):
                    if return_img:
                        from PIL import Image

                        return Image.new("RGB", (100, 100), "white")

                def df(self):
                    # Return a mock DataFrame
                    import pandas as pd

                    return pd.DataFrame(
                        [
                            ["Data 1", "Data 2", "Data 3"],
                            ["Data 4", "Data 5", "Data 6"],
                        ],
                        columns=["Header 1", "Header 2", "Header 3"],
                    )

                @property
                def caption(self):
                    return "Mock Formatted Table Caption"

            return MockFormattedTable()

    class MockTable:
        def __init__(self):
            # Mock table data for len() and indexing operations
            self._data = [
                ["Header 1", "Header 2", "Header 3"],
                ["Data 1", "Data 2", "Data 3"],
                ["Data 4", "Data 5", "Data 6"],
            ]

        def __len__(self):
            # Return number of rows for detect command
            return len(self._data)

        def __getitem__(self, index):
            # Allow indexing like table[0] for detect command
            return self._data[index]

        def visualize(self, return_img=False, **kwargs):
            if return_img:
                img = Image.new("RGB", (100, 100), "white")
                return img

        def image(self, dpi=72):
            return Image.new("RGB", (100, 100), "gray")

        @property
        def caption(self):
            return "Mock Table Caption"

    class MockConfig:
        def __init__(self):
            self.multi_header = False
            self.semantic_spanning_cells = False
            self.large_table_assumption = False
            self.verbosity = 0

    # Patch the registry to return mock components
    from gmft_cli.discovery import ComponentInfo

    def mock_get_detector(name):
        return ComponentInfo(
            name=name,
            class_type=MockDetector,
            module_path="mock.detectors",
            config_class=None,
            description="Mock detector for testing",
        )

    def mock_get_formatter(name):
        return ComponentInfo(
            name=name,
            class_type=MockFormatter,
            module_path="mock.formatters",
            config_class=MockConfig if name in ["auto", "tatr"] else None,
            description="Mock formatter for testing",
        )

    def mock_list_detectors():
        return ["auto", "tatr", "img2table"]

    def mock_list_formatters():
        return ["auto", "tatr", "ditr", "histogram", "img2table"]

    monkeypatch.setattr("gmft_cli.discovery.registry.get_detector", mock_get_detector)
    monkeypatch.setattr("gmft_cli.discovery.registry.get_formatter", mock_get_formatter)
    monkeypatch.setattr(
        "gmft_cli.discovery.registry.list_detectors", mock_list_detectors
    )
    monkeypatch.setattr(
        "gmft_cli.discovery.registry.list_formatters", mock_list_formatters
    )
    monkeypatch.setattr(
        "gmft_cli.discovery.registry.create_detector",
        lambda name, config=None: MockDetector(config),
    )
    monkeypatch.setattr(
        "gmft_cli.discovery.registry.create_formatter",
        lambda name, config=None: MockFormatter(config),
    )


def get_gmft_source_path():
    """Get path to GMFT source directory."""
    # Try to find GMFT source in various locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "gmft-source",
        Path(__file__).parent.parent.parent.parent.parent / "gmft-source",
        Path.home() / "Downloads" / "gmft-source",
        Path.home() / "gmft-source",
    ]

    for path in possible_paths:
        if path.exists() and (path / "data" / "pdfs").exists():
            return path

    # Try to find via GMFT installation
    try:
        import gmft

        gmft_path = Path(gmft.__file__).parent.parent
        if (gmft_path / "data" / "pdfs").exists():
            return gmft_path
    except Exception:
        pass

    return None


@pytest.fixture(scope="session")
def gmft_source():
    """Get GMFT source directory."""
    source_path = get_gmft_source_path()
    if not source_path:
        pytest.skip(
            "GMFT source directory not found. Clone https://github.com/conjuncts/gmft to run these tests."
        )
    return source_path


@pytest.fixture(scope="session")
def gmft_pdfs(gmft_source):
    """Get GMFT test PDFs."""
    pdfs_dir = gmft_source / "data" / "pdfs"
    if not pdfs_dir.exists():
        pytest.skip("GMFT test PDFs not found")

    pdfs = {}
    for pdf_file in pdfs_dir.glob("*.pdf"):
        pdfs[pdf_file.stem] = pdf_file

    return pdfs


@pytest.fixture(scope="session")
def gmft_references(gmft_source):
    """Get GMFT reference data."""
    ref_dir = gmft_source / "data" / "test" / "references"
    if not ref_dir.exists():
        pytest.skip("GMFT reference data not found")

    references = {}

    # Load JSON references
    for json_file in ref_dir.glob("*.json"):
        with open(json_file, "r") as f:
            references[json_file.stem] = json.load(f)

    return references
