"""Command-line interface for GMFT table detection and extraction."""

import click
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table as RichTable
from rich.progress import Progress

from .discovery import registry, get_detector_click_type, get_formatter_click_type

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="gmft-cli")
@click.option(
    "--pdf-backend",
    type=click.Choice(["auto", "pymupdf", "pypdfium2"], case_sensitive=False),
    default="auto",
    help="PDF backend to use (auto, pymupdf, pypdfium2)",
    envvar="GMFT_PDF_BACKEND",
)
@click.pass_context
def cli(ctx, pdf_backend):
    """GMFT CLI - Extract tables from PDFs and images."""
    # Store PDF backend preference in context
    ctx.ensure_object(dict)
    ctx.obj["pdf_backend"] = None if pdf_backend == "auto" else pdf_backend


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for extracted tables",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "excel", "markdown"], case_sensitive=False),
    default="csv",
    help="Output format for tables",
)
@click.option(
    "--detector",
    type=get_detector_click_type(),
    default="auto",
    help="Table detector to use",
)
@click.option(
    "--formatter",
    type=get_formatter_click_type(),
    default="auto",
    help="Table formatter to use",
)
@click.option("--pages", help="Page numbers to process (e.g., '1,3-5,7')")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--multi-header/--no-multi-header",
    default=None,
    help="Enable/disable multi-header support (TATR formatter)",
)
@click.option(
    "--semantic-spanning-cells/--no-semantic-spanning-cells",
    default=None,
    help="Enable/disable semantic spanning cells (TATR formatter)",
)
@click.option(
    "--large-table-assumption/--no-large-table-assumption",
    default=None,
    help="Enable/disable large table assumptions (TATR formatter)",
)
@click.option(
    "--captions/--no-captions",
    default=False,
    help="Extract table captions if available",
)
@click.option(
    "--visualize/--no-visualize",
    default=False,
    help="Save visualization images of detected tables",
)
@click.option(
    "--no-progress",
    is_flag=True,
    hidden=True,
    help="Disable progress display (for bulk operations)",
)
@click.pass_context
def extract(
    ctx,
    input_file: Path,
    output: Optional[Path],
    format: str,
    detector: str,
    formatter: str,
    pages: Optional[str],
    verbose: bool,
    multi_header: Optional[bool],
    semantic_spanning_cells: Optional[bool],
    large_table_assumption: Optional[bool],
    captions: bool,
    visualize: bool,
    no_progress: bool,
):
    """Extract tables from PDF or image files."""

    if not output:
        output = input_file.parent / f"{input_file.stem}_tables"

    output.mkdir(parents=True, exist_ok=True)

    console.print(f"[blue]Processing:[/blue] {input_file}")
    console.print(f"[blue]Output directory:[/blue] {output}")

    # Parse page numbers
    page_list = None
    if pages:
        page_list = parse_page_numbers(pages)
        if verbose:
            console.print(f"[dim]Processing pages: {page_list}[/dim]")

    # Select detector
    try:
        table_detector = registry.create_detector(detector)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Configure formatter based on options
    formatter_info = registry.get_formatter(formatter)
    if not formatter_info:
        console.print(f"[red]Error:[/red] Unknown formatter: {formatter}")
        sys.exit(1)

    # Create config if the formatter supports it
    config = None
    if formatter_info.config_class:
        try:
            config = formatter_info.config_class()

            # Set common config options if they exist
            if hasattr(config, "multi_header") and multi_header is not None:
                config.multi_header = multi_header
            if (
                hasattr(config, "semantic_spanning_cells")
                and semantic_spanning_cells is not None
            ):
                config.semantic_spanning_cells = semantic_spanning_cells
            if (
                hasattr(config, "large_table_assumption")
                and large_table_assumption is not None
            ):
                config.large_table_assumption = large_table_assumption
            if hasattr(config, "verbosity"):
                config.verbosity = 1 if verbose else 0
        except Exception as e:
            if verbose:
                console.print(
                    f"[yellow]Warning: Could not create config for {formatter}: {e}[/yellow]"
                )
            config = None

    try:
        table_formatter = registry.create_formatter(formatter, config)
    except Exception as e:
        console.print(f"[red]Error creating formatter:[/red] {e}")
        sys.exit(1)

    try:
        # Detect file type and process
        if input_file.suffix.lower() == ".pdf":
            pdf_backend = ctx.obj.get("pdf_backend") if ctx.obj else None
            process_pdf(
                input_file,
                output,
                format,
                table_detector,
                table_formatter,
                page_list,
                verbose,
                captions,
                visualize,
                pdf_backend,
                show_progress=not no_progress,
            )
        elif input_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            process_image(
                input_file,
                output,
                format,
                table_detector,
                table_formatter,
                verbose,
                captions,
                visualize,
            )
        else:
            console.print(
                f"[red]Error:[/red] Unsupported file type: {input_file.suffix}"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)


def parse_page_numbers(pages_str: str) -> List[int]:
    """Parse page number string (e.g., '1,3-5,7') into list of integers."""
    page_list = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            page_list.extend(range(int(start), int(end) + 1))
        else:
            page_list.append(int(part))
    return sorted(set(page_list))


def process_pdf(
    input_file: Path,
    output_dir: Path,
    format: str,
    detector,
    formatter,
    page_list: Optional[List[int]],
    verbose: bool,
    captions: bool,
    visualize: bool,
    pdf_backend: Optional[str] = None,
    show_progress: bool = True,
):
    """Process PDF file and extract tables."""
    from .pdf_handler import get_pdf_handler

    # Get PDF handler
    try:
        pdf_handler = get_pdf_handler(backend=pdf_backend)
        if verbose:
            console.print(f"[dim]Using PDF backend: {pdf_handler.backend_name}[/dim]")
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Open document using GMFT's PDF bindings
    doc = pdf_handler.open_document(input_file)

    try:
        total_pages = len(doc)

        if page_list is None:
            page_list = list(range(1, total_pages + 1))

        if show_progress:
            progress = Progress()
            progress.start()
            task = progress.add_task(
                f"Extracting tables from {len(page_list)} pages...",
                total=len(page_list),
            )
        else:
            progress = None
            task = None

        table_count = 0

        try:
            for page_num in page_list:
                if page_num < 1 or page_num > total_pages:
                    console.print(
                        f"[yellow]Warning:[/yellow] Page {page_num} out of range"
                    )
                    continue

                # Get page (0-indexed in GMFT)
                page = doc[page_num - 1]

                # Detect tables using GMFT's detector
                tables = detector.extract(page)

                if verbose and tables:
                    console.print(
                        f"[dim]Found {len(tables)} table(s) on page {page_num}[/dim]"
                    )

                # Format and save tables
                for idx, table in enumerate(tables):
                    table_count += 1

                    # Save visualization if requested
                    if visualize:
                        try:
                            # Save detection visualization
                            detect_img = table.visualize(return_img=True)
                            detect_img.save(
                                output_dir
                                / f"page_{page_num}_table_{idx + 1}_detection.png"
                            )

                            # Save cropped table image
                            table_img = table.image(dpi=144)
                            table_img.save(
                                output_dir
                                / f"page_{page_num}_table_{idx + 1}_image.png"
                            )
                        except Exception as e:
                            if verbose:
                                console.print(
                                    f"[yellow]Warning: Failed to save visualization: {e}[/yellow]"
                                )

                    # Format table
                    formatted_table = formatter.extract(table)

                    # Save formatted visualization if requested
                    if visualize and hasattr(formatted_table, "visualize"):
                        try:
                            format_img = formatted_table.visualize(
                                return_img=True, effective=True
                            )
                            format_img.save(
                                output_dir
                                / f"page_{page_num}_table_{idx + 1}_structure.png"
                            )
                        except Exception as e:
                            if verbose:
                                console.print(
                                    f"[yellow]Warning: Failed to save structure visualization: {e}[/yellow]"
                                )

                    # Extract caption if requested
                    caption = None
                    if captions and hasattr(table, "caption"):
                        caption = table.caption

                    # Get table data as list
                    table_data = formatted_table.df().values.tolist()
                    if formatted_table.df().columns.tolist():
                        # Include headers
                        table_data = [
                            formatted_table.df().columns.tolist()
                        ] + table_data

                    # Save table
                    filename = f"page_{page_num}_table_{idx + 1}"
                    save_table(
                        table_data, output_dir, filename, format, caption=caption
                    )

                if progress:
                    progress.update(task, advance=1)

            console.print(
                f"[green]✓[/green] Extracted {table_count} tables from {len(page_list)} pages"
            )

        finally:
            if progress:
                progress.stop()

    finally:
        doc.close()


def process_image(
    input_file: Path,
    output_dir: Path,
    format: str,
    detector,
    formatter,
    verbose: bool,
    captions: bool,
    visualize: bool,
):
    """Process image file and extract tables."""
    from PIL import Image

    # Load image
    img = Image.open(input_file)

    # Detect tables
    console.print("Detecting tables...")
    tables = detector.detect(img)

    if not tables:
        console.print("[yellow]No tables found in image[/yellow]")
        return

    console.print(f"Found {len(tables)} table(s)")

    # Format and save tables
    for idx, table in enumerate(tables):
        # Save visualization if requested
        if visualize:
            try:
                # Save detection visualization
                detect_img = table.visualize(return_img=True)
                detect_img.save(
                    output_dir / f"{input_file.stem}_table_{idx + 1}_detection.png"
                )

                # Save cropped table image
                table_img = table.image(dpi=144)
                table_img.save(
                    output_dir / f"{input_file.stem}_table_{idx + 1}_image.png"
                )
            except Exception as e:
                if verbose:
                    console.print(
                        f"[yellow]Warning: Failed to save visualization: {e}[/yellow]"
                    )

        # Format table
        formatted_table = formatter.format(table)

        # Save formatted visualization if requested
        if visualize and hasattr(formatted_table, "visualize"):
            try:
                format_img = formatted_table.visualize(return_img=True, effective=True)
                format_img.save(
                    output_dir / f"{input_file.stem}_table_{idx + 1}_structure.png"
                )
            except Exception as e:
                if verbose:
                    console.print(
                        f"[yellow]Warning: Failed to save structure visualization: {e}[/yellow]"
                    )

        # Extract caption if requested
        caption = None
        if captions and hasattr(table, "caption"):
            caption = table.caption

        # Save table
        filename = f"{input_file.stem}_table_{idx + 1}"
        save_table(formatted_table, output_dir, filename, format, caption=caption)

    console.print(f"[green]✓[/green] Extracted {len(tables)} tables")


def save_table(
    table_data,
    output_dir: Path,
    filename: str,
    format: str,
    caption: Optional[str] = None,
):
    """Save table data in specified format."""
    output_file = output_dir / f"{filename}.{format}"

    # Save caption if provided
    if caption:
        caption_file = output_dir / f"{filename}_caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)

    if format == "csv":
        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(table_data)

    elif format == "json":
        import json

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(table_data, f, indent=2, ensure_ascii=False)

    elif format == "excel":
        try:
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            for row in table_data:
                ws.append(row)
            wb.save(output_file)
        except ImportError:
            console.print(
                "[red]Error:[/red] openpyxl not installed. Install with: pip install openpyxl"
            )
            sys.exit(1)

    elif format == "markdown":
        with open(output_file, "w", encoding="utf-8") as f:
            if table_data:
                # Header
                f.write("| " + " | ".join(str(cell) for cell in table_data[0]) + " |\n")
                f.write("|" + "|".join("---" for _ in table_data[0]) + "|\n")

                # Rows
                for row in table_data[1:]:
                    f.write("| " + " | ".join(str(cell) for cell in row) + " |\n")


@cli.command()
@click.argument(
    "input_files",
    nargs=-1,
    required=False,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for extracted tables",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "excel", "markdown"], case_sensitive=False),
    default="csv",
    help="Output format for tables",
)
@click.option(
    "--detector",
    type=get_detector_click_type(),
    default="auto",
    help="Table detector to use",
)
@click.option(
    "--formatter",
    type=get_formatter_click_type(),
    default="auto",
    help="Table formatter to use",
)
@click.option("--pattern", help="Glob pattern to find files (e.g., '*.pdf')")
@click.option("--recursive", "-r", is_flag=True, help="Search for files recursively")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--keyword-filter",
    help="Only process pages containing specific keywords (comma-separated)",
)
def bulk_extract(
    input_files: tuple,
    output: Optional[Path],
    format: str,
    detector: str,
    formatter: str,
    pattern: Optional[str],
    recursive: bool,
    verbose: bool,
    keyword_filter: Optional[str],
):
    """Extract tables from multiple PDF or image files."""
    from glob import glob

    # Collect all files to process
    files_to_process = []

    if pattern:
        # Use glob pattern
        if recursive:
            pattern = f"**/{pattern}"
        matched_files = glob(pattern, recursive=recursive)
        files_to_process.extend([Path(f) for f in matched_files])

    # Add explicitly provided files
    files_to_process.extend(input_files)

    # Remove duplicates and sort
    files_to_process = sorted(set(files_to_process))

    # Validate that we have either input files or pattern
    if not input_files and not pattern:
        console.print("[red]Error:[/red] Must provide either input files or --pattern")
        sys.exit(1)

    if not files_to_process:
        console.print("[yellow]No files found to process[/yellow]")
        return

    console.print(f"[blue]Found {len(files_to_process)} files to process[/blue]")

    # Set up output directory
    if not output:
        output = Path("bulk_extracted_tables")
    output.mkdir(parents=True, exist_ok=True)

    # Parse keywords
    keywords = []
    if keyword_filter:
        keywords = [k.strip().lower() for k in keyword_filter.split(",")]
        console.print(
            f"[blue]Filtering pages with keywords:[/blue] {', '.join(keywords)}"
        )

    # Process each file
    total_tables = 0
    with Progress() as progress:
        task = progress.add_task(
            f"Processing {len(files_to_process)} files...", total=len(files_to_process)
        )

        for file_path in files_to_process:
            if verbose:
                console.print(f"\n[dim]Processing: {file_path}[/dim]")

            # Create subdirectory for this file's tables
            file_output = output / file_path.stem
            file_output.mkdir(exist_ok=True)

            # Extract tables using the existing extract logic
            try:
                # For PDFs with keyword filter, determine which pages to process
                pages_to_process = None
                if keyword_filter and file_path.suffix.lower() == ".pdf":
                    from .pdf_handler import get_pdf_handler

                    try:
                        pdf_handler = get_pdf_handler()
                        pages_to_process = []

                        for page_num in range(pdf_handler.get_page_count(file_path)):
                            text = pdf_handler.extract_page_text(
                                file_path, page_num
                            ).lower()

                            # Check if any keyword is in the page
                            if any(keyword in text for keyword in keywords):
                                pages_to_process.append(page_num + 1)

                        if not pages_to_process:
                            if verbose:
                                console.print(
                                    f"[yellow]No pages with keywords found in {file_path}[/yellow]"
                                )
                            continue

                        # Convert to page string
                        pages_str = ",".join(str(p) for p in pages_to_process)
                        if verbose:
                            console.print(
                                f"[dim]Pages with keywords: {pages_str}[/dim]"
                            )
                    except ImportError as e:
                        console.print(
                            f"[yellow]Warning: Could not filter by keywords - {e}[/yellow]"
                        )
                        pages_str = None
                else:
                    pages_str = None

                ctx = click.Context(extract)
                ctx.invoke(
                    extract,
                    input_file=file_path,
                    output=file_output,
                    format=format,
                    detector=detector,
                    formatter=formatter,
                    pages=pages_str,
                    verbose=verbose,
                    multi_header=None,
                    semantic_spanning_cells=None,
                    large_table_assumption=None,
                    captions=False,
                    visualize=False,
                    no_progress=True,
                )

                # Count extracted tables
                table_files = list(file_output.glob(f"*.{format}"))
                total_tables += len(table_files)

            except (Exception, SystemExit) as e:
                error_msg = (
                    str(e)
                    if not isinstance(e, SystemExit)
                    else f"Command failed with exit code {e.code}"
                )
                console.print(f"[red]Error processing {file_path}:[/red] {error_msg}")
                if verbose:
                    console.print_exception()

            progress.update(task, advance=1)

    console.print(
        f"\n[green]✓[/green] Extracted {total_tables} tables from {len(files_to_process)} files"
    )
    console.print(f"[green]Output saved to:[/green] {output}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--detector",
    type=get_detector_click_type(),
    default="auto",
    help="Table detector to use",
)
def detect(input_file: Path, detector: str):
    """Detect tables in PDF or image files without extraction."""

    console.print(f"[blue]Detecting tables in:[/blue] {input_file}")

    # Select detector
    try:
        table_detector = registry.create_detector(detector)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    try:
        if input_file.suffix.lower() == ".pdf":
            detect_pdf_tables(input_file, table_detector)
        elif input_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            detect_image_tables(input_file, table_detector)
        else:
            console.print(
                f"[red]Error:[/red] Unsupported file type: {input_file.suffix}"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        console.print_exception()
        sys.exit(1)


def detect_pdf_tables(input_file: Path, detector):
    """Detect tables in PDF and display summary."""
    from .pdf_handler import get_pdf_handler

    # Get PDF handler
    try:
        pdf_handler = get_pdf_handler()
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    doc = pdf_handler.open_document(input_file)

    try:
        total_tables = 0

        # Create summary table
        summary = RichTable(title="Table Detection Results")
        summary.add_column("Page", style="cyan")
        summary.add_column("Tables Found", style="green")
        summary.add_column("Table Dimensions", style="yellow")

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Detect tables
            tables = detector.extract(page)

            if tables:
                total_tables += len(tables)
                dimensions = []
                for t in tables:
                    try:
                        # Try to get dimensions from formatted table
                        ft = t.to_dict() if hasattr(t, "to_dict") else t
                        if hasattr(ft, "shape"):
                            dimensions.append(f"{ft.shape[0]}x{ft.shape[1]}")
                        else:
                            dimensions.append("Unknown")
                    except Exception:
                        dimensions.append("Unknown")

                summary.add_row(
                    str(page_num + 1), str(len(tables)), ", ".join(dimensions)
                )

        console.print(summary)
        console.print(f"\n[green]Total tables found:[/green] {total_tables}")

    finally:
        doc.close()


def detect_image_tables(input_file: Path, detector):
    """Detect tables in image and display summary."""
    from PIL import Image

    img = Image.open(input_file)
    tables = detector.detect(img)

    if not tables:
        console.print("[yellow]No tables found in image[/yellow]")
        return

    # Create summary table
    summary = RichTable(title="Table Detection Results")
    summary.add_column("Table #", style="cyan")
    summary.add_column("Dimensions", style="green")
    summary.add_column("Location", style="yellow")

    for idx, table in enumerate(tables):
        summary.add_row(
            str(idx + 1), f"{len(table)}x{len(table[0]) if table else 0}", "Full image"
        )

    console.print(summary)
    console.print(f"\n[green]Total tables found:[/green] {len(tables)}")


@cli.command()
def pdf_backends():
    """Show available PDF backends and their status."""
    from .pdf_handler import list_pdf_backends

    list_pdf_backends()


@cli.command()
def list_components():
    """List all available detectors and formatters."""
    registry.discover()

    # List detectors
    console.print("\n[bold blue]Available Detectors:[/bold blue]")
    detector_table = RichTable(show_header=True, header_style="bold")
    detector_table.add_column("Name", style="cyan")
    detector_table.add_column("Module", style="dim")
    detector_table.add_column("Description")

    for name in registry.list_detectors():
        info = registry.get_detector(name)
        detector_table.add_row(
            name, info.module_path, info.description or "No description available"
        )

    console.print(detector_table)

    # List formatters
    console.print("\n[bold blue]Available Formatters:[/bold blue]")
    formatter_table = RichTable(show_header=True, header_style="bold")
    formatter_table.add_column("Name", style="cyan")
    formatter_table.add_column("Module", style="dim")
    formatter_table.add_column("Has Config", style="green")
    formatter_table.add_column("Description")

    for name in registry.list_formatters():
        info = registry.get_formatter(name)
        formatter_table.add_row(
            name,
            info.module_path,
            "✓" if info.config_class else "✗",
            info.description or "No description available",
        )

    console.print(formatter_table)

    # Show formatter config options
    console.print("\n[bold blue]Formatter Configuration Options:[/bold blue]")
    for name in registry.list_formatters():
        options = registry.get_formatter_config_options(name)
        if options:
            console.print(f"\n[cyan]{name}[/cyan] formatter options:")
            for opt_name, default, desc in options:
                default_str = f" (default: {default})" if default is not None else ""
                console.print(f"  --{opt_name.replace('_', '-')}: {desc}{default_str}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
