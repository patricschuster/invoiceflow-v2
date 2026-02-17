"""
File Service for handling file uploads, validation, and storage
"""

from pathlib import Path
from datetime import datetime
import uuid
import shutil
import logging
from typing import Optional, Tuple

from fastapi import UploadFile
import filetype

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations (upload, validation, storage)"""

    # Maximum file size: 50MB
    MAX_FILE_SIZE = 52428800

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.xml'}

    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/xml',
        'application/xml',
    }

    @staticmethod
    async def validate_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded file

        Args:
            file: FastAPI UploadFile object

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file:
            return False, "No file provided"

        # Check filename
        if not file.filename:
            return False, "Filename is empty"

        # Check file extension
        file_path = Path(file.filename)
        file_extension = file_path.suffix.lower()

        if file_extension not in FileService.ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension: {file_extension}. Allowed: {', '.join(FileService.ALLOWED_EXTENSIONS)}"

        # Check content type (MIME type)
        if file.content_type and file.content_type not in FileService.ALLOWED_MIME_TYPES:
            logger.warning(f"Suspicious content type: {file.content_type} for file {file.filename}")
            # Don't reject yet, check actual file content

        # Read file content for validation
        try:
            # Read first chunk to check file type
            content_start = await file.read(8192)  # Read first 8KB

            # Reset file pointer
            await file.seek(0)

            # Check file size
            file_size = 0
            chunk_size = 8192
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)

                # Check if file is too large
                if file_size > FileService.MAX_FILE_SIZE:
                    await file.seek(0)
                    return False, f"File too large: {file_size} bytes. Maximum: {FileService.MAX_FILE_SIZE} bytes (50MB)"

            # Reset file pointer for saving
            await file.seek(0)

            # Verify file type by content (magic bytes)
            detected_type = filetype.guess(content_start)

            if file_extension == '.pdf':
                # Check if it's actually a PDF
                if detected_type and detected_type.mime != 'application/pdf':
                    # Check for PDF magic bytes manually
                    if not content_start.startswith(b'%PDF'):
                        return False, f"File does not appear to be a valid PDF (detected: {detected_type.mime if detected_type else 'unknown'})"

            elif file_extension == '.xml':
                # Check if it looks like XML
                if not content_start.strip().startswith(b'<?xml') and not content_start.strip().startswith(b'<'):
                    return False, "File does not appear to be a valid XML"

            logger.info(f"File validation passed: {file.filename} ({file_size} bytes)")
            return True, ""

        except Exception as e:
            logger.error(f"Error validating file {file.filename}: {e}")
            return False, f"File validation error: {str(e)}"

    @staticmethod
    async def save_uploaded_file(file: UploadFile, destination_dir: Path) -> Path:
        """
        Save uploaded file with unique filename

        Args:
            file: FastAPI UploadFile object
            destination_dir: Directory to save file

        Returns:
            Path to saved file

        Raises:
            IOError: If file cannot be saved
        """
        try:
            # Ensure destination directory exists
            destination_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            original_filename = Path(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_extension = original_filename.suffix.lower()

            # Clean original filename (remove special characters)
            clean_name = "".join(
                c for c in original_filename.stem if c.isalnum() or c in (' ', '-', '_')
            ).strip()
            clean_name = clean_name[:50]  # Limit length

            # Construct new filename: timestamp_uuid_originalname.ext
            new_filename = f"{timestamp}_{unique_id}_{clean_name}{file_extension}"
            destination_path = destination_dir / new_filename

            # Save file
            logger.info(f"Saving file to: {destination_path}")
            with open(destination_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            logger.info(f"File saved successfully: {destination_path} ({len(content)} bytes)")
            return destination_path

        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise IOError(f"Failed to save file: {str(e)}")

    @staticmethod
    def get_file_type(file_path: Path) -> str:
        """
        Detect invoice file type

        Args:
            file_path: Path to file

        Returns:
            File type: 'zugferd', 'xrechnung', 'pdf', 'xml', 'unknown'
        """
        try:
            file_extension = file_path.suffix.lower()

            if file_extension == '.pdf':
                # Check if PDF contains embedded XML (ZUGFeRD indicator)
                if FileService._has_embedded_xml(file_path):
                    return 'zugferd'
                return 'pdf'

            elif file_extension == '.xml':
                # Check if it's XRechnung
                if FileService._is_xrechnung_xml(file_path):
                    return 'xrechnung'
                return 'xml'

            return 'unknown'

        except Exception as e:
            logger.error(f"Error detecting file type for {file_path}: {e}")
            return 'unknown'

    @staticmethod
    def _has_embedded_xml(pdf_path: Path) -> bool:
        """
        Check if PDF contains embedded XML (ZUGFeRD/Factur-X indicator)

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF contains embedded XML
        """
        try:
            # Try using factur-x to check for embedded XML
            try:
                from facturx import get_facturx_xml_from_pdf
                xml_content = get_facturx_xml_from_pdf(str(pdf_path))
                return xml_content is not None and len(xml_content) > 0
            except ImportError:
                # Fallback: Simple check in PDF content
                pass

            # Fallback: Check PDF content for XML attachment indicators
            with open(pdf_path, 'rb') as f:
                content = f.read(50000)  # Read first 50KB
                # Look for common ZUGFeRD/Factur-X indicators
                indicators = [
                    b'/EmbeddedFiles',
                    b'factur-x.xml',
                    b'zugferd-invoice.xml',
                    b'xrechnung.xml',
                ]
                return any(indicator in content for indicator in indicators)

        except Exception as e:
            logger.error(f"Error checking for embedded XML in {pdf_path}: {e}")
            return False

    @staticmethod
    def _is_xrechnung_xml(xml_path: Path) -> bool:
        """
        Check if XML file is XRechnung format

        Args:
            xml_path: Path to XML file

        Returns:
            True if file appears to be XRechnung
        """
        try:
            with open(xml_path, 'rb') as f:
                content = f.read(5000)  # Read first 5KB

                # Look for XRechnung-specific namespaces
                xrechnung_indicators = [
                    b'urn:oasis:names:specification:ubl:schema:xsd:Invoice',
                    b'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice',
                    b'XRechnung',
                ]

                return any(indicator in content for indicator in xrechnung_indicators)

        except Exception as e:
            logger.error(f"Error checking if {xml_path} is XRechnung: {e}")
            return False

    @staticmethod
    def move_file(source: Path, destination: Path) -> Path:
        """
        Move file from source to destination

        Args:
            source: Source file path
            destination: Destination file path or directory

        Returns:
            Path to moved file

        Raises:
            IOError: If file cannot be moved
        """
        try:
            # If destination is a directory, preserve filename
            if destination.is_dir():
                destination = destination / source.name

            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            logger.info(f"Moving file from {source} to {destination}")
            shutil.move(str(source), str(destination))

            logger.info(f"File moved successfully to: {destination}")
            return destination

        except Exception as e:
            logger.error(f"Error moving file from {source} to {destination}: {e}")
            raise IOError(f"Failed to move file: {str(e)}")

    @staticmethod
    def delete_file(file_path: Path) -> bool:
        """
        Delete file

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted successfully
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """
        Get file information

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        try:
            if not file_path.exists():
                return {
                    'exists': False,
                    'error': 'File not found'
                }

            stat = file_path.stat()

            return {
                'exists': True,
                'name': file_path.name,
                'size': stat.st_size,
                'extension': file_path.suffix,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'type': FileService.get_file_type(file_path),
            }

        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
