# GMFT CLI

Command-line interface for GMFT (General Multi Format Table) detection and extraction from PDFs and images.

This CLI automatically discovers and uses all available detectors and formatters from the installed GMFT package, so it stays up-to-date with new components added to GMFT.

## Installation

```bash
# Install from source (without PDF backend)
pip install -e .

# Install with PyMuPDF (recommended by GMFT for best performance)
pip install -e ".[pdf-pymupdf]"

# Install with pypdfium2 (lighter alternative)
pip install -e ".[pdf-pypdfium2]"

# Install with both PDF backends
pip install -e ".[pdf-all]"

# Or install with uv
uv pip install -e .
uv pip install pypdfium2  # or PyMuPDF
```

### PDF Backend Support

GMFT CLI dynamically uses the PDF backends available in your environment:
- **PyMuPDF** (recommended by GMFT): Best performance, accuracy, and advanced line break detection. Requires AGPL-3.0 license compliance.
- **pypdfium2**: Lighter alternative with good compatibility, but less accurate line detection compared to PyMuPDF.

The CLI will automatically detect and use whichever backend is available. You can also specify which backend to use with the `--pdf-backend` option or the `GMFT_PDF_BACKEND` environment variable.

**Note**: GMFT officially recommends PyMuPDF for optimal performance and accuracy, especially for complex PDFs with intricate line structures. However, pypdfium2 is included as a lighter alternative that doesn't require AGPL license compliance.

## Usage

### Extract Tables

Extract tables from PDF or image files:

```bash
# Extract tables from PDF (all pages, CSV format)
gmft-cli extract document.pdf

# Extract specific pages with custom output format
gmft-cli extract document.pdf --pages 1,3-5 --format json -o output_dir/

# Extract from image with different formatters
gmft-cli extract image.png --formatter histogram --format markdown

# Extract with visualization and captions
gmft-cli extract paper.pdf --visualize --captions -o results/

# Extract with TATR formatter configuration
gmft-cli extract complex.pdf --formatter tatr --multi-header --semantic-spanning-cells

# List all available components
gmft-cli list-components

# Check PDF backend status
gmft-cli pdf-backends

# Use specific PDF backend (PyMuPDF recommended for best performance)
gmft-cli --pdf-backend pymupdf extract document.pdf

# Or set via environment variable  
export GMFT_PDF_BACKEND=pymupdf
gmft-cli extract document.pdf

# Available formats: csv, json, excel, markdown
# Detectors and formatters are discovered dynamically from your GMFT installation
```

### Bulk Extract

Process multiple files at once:

```bash
# Extract from multiple files
gmft-cli bulk-extract file1.pdf file2.pdf file3.pdf

# Extract from all PDFs in directory
gmft-cli bulk-extract --pattern "*.pdf" -o bulk_results/

# Recursive search with keyword filtering
gmft-cli bulk-extract --pattern "*.pdf" --recursive --keyword-filter "table,figure,results"

# Mix pattern and explicit files
gmft-cli bulk-extract report.pdf --pattern "papers/*.pdf" --format json
```

### Detect Tables

Detect tables without extraction (useful for previewing):

```bash
# Detect tables in PDF
gmft-cli detect document.pdf

# Detect with specific detector
gmft-cli detect image.jpg --detector tatr
```

### List Components

See all available detectors and formatters:

```bash
# List all available components with descriptions
gmft-cli list-components
```

## Options

### Extract Command

- `INPUT_FILE`: Path to PDF or image file
- `-o, --output`: Output directory for extracted tables (default: `{filename}_tables/`)
- `-f, --format`: Output format - csv, json, excel, markdown (default: csv)
- `--detector`: Table detector to use (run `gmft-cli list-components` to see available options)
- `--formatter`: Table formatter to use (run `gmft-cli list-components` to see available options)
- `--pages`: Page numbers to process, e.g., '1,3-5,7' (PDF only)
- `-v, --verbose`: Enable verbose output
- `--multi-header/--no-multi-header`: Enable/disable multi-header support (TATR formatter)
- `--semantic-spanning-cells/--no-semantic-spanning-cells`: Enable/disable semantic spanning cells (TATR formatter)
- `--large-table-assumption/--no-large-table-assumption`: Enable/disable large table assumptions (TATR formatter)
- `--captions/--no-captions`: Extract table captions if available
- `--visualize/--no-visualize`: Save visualization images of detected tables

### Bulk Extract Command

- `INPUT_FILES`: One or more files to process
- `-o, --output`: Output directory (default: `bulk_extracted_tables/`)
- `-f, --format`: Output format - csv, json, excel, markdown (default: csv)
- `--detector`: Table detector to use (run `gmft-cli list-components` to see available options)
- `--formatter`: Table formatter to use (run `gmft-cli list-components` to see available options)
- `--pattern`: Glob pattern to find files (e.g., '*.pdf')
- `-r, --recursive`: Search for files recursively
- `-v, --verbose`: Enable verbose output
- `--keyword-filter`: Only process pages containing specific keywords (comma-separated)

### Detect Command

- `INPUT_FILE`: Path to PDF or image file  
- `--detector`: Table detector to use (run `gmft-cli list-components` to see available options)

## Examples

```bash
# Extract all tables from a PDF as CSV files
gmft-cli extract report.pdf

# Extract tables from specific pages as JSON
gmft-cli extract report.pdf --pages 2-10 --format json

# Extract tables from an image as markdown
gmft-cli extract screenshot.png --format markdown -o tables/

# Use the fast histogram formatter for quick extraction
gmft-cli extract document.pdf --formatter histogram

# Extract with all visualizations and captions
gmft-cli extract research_paper.pdf --visualize --captions --verbose

# Bulk extract from directory with keyword filtering
gmft-cli bulk-extract --pattern "papers/**/*.pdf" --recursive --keyword-filter "experiment,results"

# Just detect tables to see what's available
gmft-cli detect presentation.pdf
```

## Component Discovery

The CLI automatically discovers all available detectors and formatters from your GMFT installation. This means:

- New components added to GMFT are automatically available in the CLI
- No need to update the CLI when GMFT adds new detectors or formatters
- Configuration options are discovered dynamically from each component

Run `gmft-cli list-components` to see all available components and their configuration options.

## Supported File Types

- PDF files (`.pdf`)
- Images: PNG, JPG, JPEG, BMP, TIFF

## Output Formats

- **CSV**: Comma-separated values
- **JSON**: Structured JSON arrays
- **Excel**: Excel workbook (.xlsx)
- **Markdown**: Markdown tables

## Output Structure

When extracting tables, the CLI creates:
- `{filename}.{format}`: The extracted table data
- `{filename}_caption.txt`: Caption text (if --captions enabled)
- `{filename}_detection.png`: Visualization of detected table region (if --visualize enabled)
- `{filename}_image.png`: Cropped table image at high DPI (if --visualize enabled)
- `{filename}_structure.png`: Visualization of table structure (if --visualize enabled)

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```