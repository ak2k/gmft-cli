"""Dynamic PDF handling using GMFT's PDF bindings."""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class PDFBackendInfo:
    """Information about available PDF backend."""

    name: str
    module: str
    available: bool
    error: Optional[str] = None


class PDFHandler:
    """Handle PDF operations using GMFT's PDF bindings."""

    def __init__(self, backend: Optional[str] = None):
        """Initialize PDF handler with optional backend selection.

        Args:
            backend: 'pymupdf', 'pypdfium2', or None for auto-detection
        """
        self.backend = backend
        self._document_class = None
        self._backend_info = None
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the PDF backend using GMFT's bindings."""
        backends_to_try = []

        if self.backend:
            # User specified a backend
            backends_to_try = [self.backend]
        else:
            # Try in GMFT's preferred order
            backends_to_try = ["pypdfium2", "pymupdf"]

        errors = {}

        for backend_name in backends_to_try:
            try:
                if backend_name == "pypdfium2":
                    from gmft.pdf_bindings import PyPDFium2Document

                    self._document_class = PyPDFium2Document
                    self._backend_info = PDFBackendInfo(
                        name="pypdfium2",
                        module="gmft.pdf_bindings.PyPDFium2Document",
                        available=True,
                    )
                    return
                elif backend_name == "pymupdf":
                    from gmft.pdf_bindings import PyMuPDFDocument

                    self._document_class = PyMuPDFDocument
                    self._backend_info = PDFBackendInfo(
                        name="pymupdf",
                        module="gmft.pdf_bindings.PyMuPDFDocument",
                        available=True,
                    )
                    return
            except ImportError as e:
                errors[backend_name] = str(e)
                continue

        # No backend available
        if self.backend:
            # User requested specific backend that's not available
            raise ImportError(
                f"Requested PDF backend '{self.backend}' is not available. "
                f"Error: {errors.get(self.backend, 'Unknown error')}"
            )
        else:
            # No backend available at all
            raise ImportError(
                "No PDF backend available. Please install either 'pypdfium2' or 'PyMuPDF':\n"
                "  pip install pypdfium2\n"
                "  or\n"
                "  pip install PyMuPDF"
            )

    @property
    def backend_name(self) -> str:
        """Get the name of the current backend."""
        return self._backend_info.name if self._backend_info else "none"

    @property
    def is_available(self) -> bool:
        """Check if a PDF backend is available."""
        return self._document_class is not None

    def open_document(self, pdf_path: Path):
        """Open a PDF document using GMFT's bindings.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            GMFT PDF document object
        """
        if not self._document_class:
            raise RuntimeError("No PDF backend initialized")

        return self._document_class(str(pdf_path))

    def get_page_count(self, pdf_path: Path) -> int:
        """Get the number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages
        """
        doc = self.open_document(pdf_path)
        try:
            return len(doc)
        finally:
            doc.close()

    def extract_page_text(self, pdf_path: Path, page_num: int) -> str:
        """Extract text from a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Text content of the page
        """
        doc = self.open_document(pdf_path)
        try:
            page = doc[page_num]
            # Try GMFT's method first
            if hasattr(page, "get_text"):
                return page.get_text()
            # Fallback for different backends
            elif hasattr(page, "text"):
                return page.text
            else:
                return ""
        finally:
            doc.close()

    @staticmethod
    def check_available_backends() -> List[PDFBackendInfo]:
        """Check which PDF backends are available.

        Returns:
            List of backend information
        """
        backends = []

        # Check pypdfium2
        try:
            from gmft.pdf_bindings import PyPDFium2Document

            # Verify the class is usable
            _ = PyPDFium2Document
            backends.append(
                PDFBackendInfo(
                    name="pypdfium2",
                    module="gmft.pdf_bindings.PyPDFium2Document",
                    available=True,
                )
            )
        except ImportError as e:
            backends.append(
                PDFBackendInfo(
                    name="pypdfium2",
                    module="gmft.pdf_bindings.PyPDFium2Document",
                    available=False,
                    error=str(e),
                )
            )

        # Check PyMuPDF
        try:
            from gmft.pdf_bindings import PyMuPDFDocument

            # Verify the class is usable
            _ = PyMuPDFDocument
            backends.append(
                PDFBackendInfo(
                    name="pymupdf",
                    module="gmft.pdf_bindings.PyMuPDFDocument",
                    available=True,
                )
            )
        except ImportError as e:
            backends.append(
                PDFBackendInfo(
                    name="pymupdf",
                    module="gmft.pdf_bindings.PyMuPDFDocument",
                    available=False,
                    error=str(e),
                )
            )

        return backends


# Global PDF handler instance
_pdf_handler = None


def get_pdf_handler(backend: Optional[str] = None) -> PDFHandler:
    """Get or create a PDF handler instance.

    Args:
        backend: Optional backend to use ('pymupdf', 'pypdfium2', or None for auto)

    Returns:
        PDFHandler instance
    """
    global _pdf_handler

    if _pdf_handler is None or (backend and _pdf_handler.backend_name != backend):
        _pdf_handler = PDFHandler(backend)

    return _pdf_handler


def list_pdf_backends():
    """List available PDF backends with their status."""
    backends = PDFHandler.check_available_backends()

    print("PDF Backend Status:")
    print("-" * 50)

    for backend in backends:
        status = "✓ Available" if backend.available else "✗ Not available"
        print(f"{backend.name:12} {status}")
        if not backend.available and backend.error:
            print(f"             Error: {backend.error}")

    # Show current backend
    try:
        handler = get_pdf_handler()
        print(f"\nCurrent backend: {handler.backend_name}")
    except ImportError:
        print("\nNo PDF backend currently available")


if __name__ == "__main__":
    # If run directly, show backend status
    list_pdf_backends()
