"""
Invoice Parser Service for ZUGFeRD and XRechnung formats
"""

from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass, field
import logging

try:
    # factur-x 3.x API (no dict conversion, only XML extraction)
    from facturx import get_xml_from_pdf, get_facturx_level
    get_facturx_xml_from_pdf = get_xml_from_pdf  # Alias for compatibility
    facturx_available = True
    facturx_version = 3
except ImportError:
    try:
        # Fallback to old API (factur-x < 3.0)
        from facturx import get_facturx_xml_from_pdf
        facturx_available = True
        facturx_version = 2
    except ImportError:
        # Fallback if factur-x is not installed
        get_facturx_xml_from_pdf = None
        facturx_available = False
        facturx_version = None

from lxml import etree

logger = logging.getLogger(__name__)


@dataclass
class InvoiceData:
    """Structured invoice data extracted from ZUGFeRD/XRechnung"""

    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    supplier_name: Optional[str] = None
    supplier_id: Optional[str] = None  # Tax ID or vendor number
    supplier_email: Optional[str] = None  # Contact email (DefinedTradeContact)
    supplier_electronic_address: Optional[str] = None  # Electronic address (URIUniversalCommunication)
    amount_net: Optional[Decimal] = None
    amount_gross: Optional[Decimal] = None
    amount_vat: Optional[Decimal] = None
    currency: str = "EUR"

    # Metadata
    extraction_errors: list[str] = field(default_factory=list)
    extraction_warnings: list[str] = field(default_factory=list)
    raw_xml: Optional[str] = None
    detected_format: Optional[str] = None  # 'zugferd', 'xrechnung', 'unknown'


class InvoiceParser:
    """Parser for ZUGFeRD and XRechnung invoice formats"""

    @staticmethod
    def parse_invoice(file_path: Path) -> InvoiceData:
        """
        Main entry point - parse invoice file and extract data

        Args:
            file_path: Path to PDF or XML file

        Returns:
            InvoiceData object with extracted information
        """
        invoice_data = InvoiceData()

        try:
            # Detect file type
            file_extension = file_path.suffix.lower()

            if file_extension == '.pdf':
                logger.info(f"Parsing PDF file: {file_path}")
                invoice_data = InvoiceParser.parse_zugferd(file_path)
            elif file_extension == '.xml':
                logger.info(f"Parsing XML file: {file_path}")
                invoice_data = InvoiceParser.parse_xrechnung(file_path)
            else:
                invoice_data.extraction_errors.append(
                    f"Unsupported file extension: {file_extension}"
                )
                invoice_data.detected_format = "unknown"

        except Exception as e:
            logger.error(f"Error parsing invoice {file_path}: {e}")
            invoice_data.extraction_errors.append(f"Parsing failed: {str(e)}")

        return invoice_data

    @staticmethod
    def parse_zugferd(pdf_path: Path) -> InvoiceData:
        """
        Parse ZUGFeRD PDF (PDF with embedded XML)

        Args:
            pdf_path: Path to ZUGFeRD PDF file

        Returns:
            InvoiceData object with extracted information
        """
        invoice_data = InvoiceData(detected_format="zugferd")

        if not facturx_available:
            invoice_data.extraction_errors.append(
                "factur-x library not installed. Cannot parse ZUGFeRD."
            )
            return invoice_data

        try:
            # Extract XML from PDF using factur-x 3.x API
            logger.info(f"Extracting XML from ZUGFeRD PDF: {pdf_path}")

            # Read PDF file as bytes (factur-x 3.x expects bytes)
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            # Try new API (factur-x 3.x) - expects bytes, returns tuple (filename, xml_bytes)
            try:
                result = get_xml_from_pdf(pdf_bytes)
                # factur-x 3.x returns a tuple: (filename, xml_content)
                if isinstance(result, tuple):
                    xml_filename, xml_content = result
                    logger.info(f"XML extracted successfully from {xml_filename} using factur-x 3.x API")
                else:
                    xml_content = result
                    logger.info(f"XML extracted successfully using factur-x old API")
            except NameError:
                # Fallback to old API - might expect path
                xml_content = get_facturx_xml_from_pdf(str(pdf_path))
                logger.info(f"XML extracted successfully using factur-x old API")

            if not xml_content:
                invoice_data.extraction_errors.append(
                    "No embedded XML found in PDF. This may not be a ZUGFeRD file."
                )
                logger.warning(f"No XML found in PDF: {pdf_path}")
                return invoice_data

            # Store raw XML for debugging
            if isinstance(xml_content, bytes):
                invoice_data.raw_xml = xml_content.decode('utf-8')
            else:
                invoice_data.raw_xml = xml_content

            logger.info(f"XML content length: {len(invoice_data.raw_xml)} chars")

            # factur-x 3.x doesn't have xml_to_dict, so parse XML manually
            logger.info("Parsing ZUGFeRD XML data manually")

            try:
                root = etree.fromstring(invoice_data.raw_xml.encode('utf-8'))
                logger.info(f"XML root tag: {root.tag}")

                # Parse based on XML format
                # Check if it's CII format (ZUGFeRD/Factur-X standard)
                if 'CrossIndustryInvoice' in root.tag:
                    logger.info("Detected CII (Cross Industry Invoice) format")
                    invoice_data = InvoiceParser._extract_from_cii_xml(root, invoice_data)
                # Check if it's UBL format
                elif 'Invoice' in root.tag and 'oasis' in root.tag:
                    logger.info("Detected UBL format")
                    invoice_data = InvoiceParser._extract_from_ubl_xml(root, invoice_data)
                else:
                    logger.warning(f"Unknown XML format, trying generic extraction. Root tag: {root.tag}")
                    invoice_data = InvoiceParser._extract_from_cii_xml(root, invoice_data)

            except etree.XMLSyntaxError as e:
                logger.error(f"XML parsing failed: {e}")
                invoice_data.extraction_errors.append(f"Invalid XML syntax: {str(e)}")
            except Exception as e:
                logger.error(f"Manual XML parsing failed: {e}", exc_info=True)
                invoice_data.extraction_errors.append(f"XML parsing error: {str(e)}")

        except FileNotFoundError:
            invoice_data.extraction_errors.append(f"File not found: {pdf_path}")
            logger.error(f"File not found: {pdf_path}")
        except Exception as e:
            logger.error(f"Error parsing ZUGFeRD PDF {pdf_path}: {e}", exc_info=True)
            invoice_data.extraction_errors.append(f"ZUGFeRD parsing error: {str(e)}")

        return invoice_data

    @staticmethod
    def parse_xrechnung(xml_path: Path) -> InvoiceData:
        """
        Parse XRechnung XML file

        Args:
            xml_path: Path to XRechnung XML file

        Returns:
            InvoiceData object with extracted information
        """
        invoice_data = InvoiceData(detected_format="xrechnung")

        try:
            # Read XML file
            logger.info(f"Reading XRechnung XML: {xml_path}")
            with open(xml_path, 'rb') as f:
                xml_content = f.read()

            # Store raw XML
            invoice_data.raw_xml = xml_content.decode('utf-8')

            # Parse XML
            root = etree.fromstring(xml_content)

            # Detect namespace (UBL or CII)
            namespace = root.nsmap.get(None, '')

            if 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice' in namespace:
                # CII format - can use factur-x
                logger.info("Detected CII format XRechnung")
                if get_facturx_dict:
                    facturx_dict = get_facturx_dict(str(xml_path))
                    if facturx_dict:
                        invoice_data = InvoiceParser._extract_from_facturx_dict(facturx_dict, invoice_data)
                    else:
                        # Fallback to manual parsing
                        invoice_data = InvoiceParser._extract_from_cii_xml(root, invoice_data)
                else:
                    invoice_data = InvoiceParser._extract_from_cii_xml(root, invoice_data)

            elif 'urn:oasis:names:specification:ubl:schema:xsd:Invoice' in namespace:
                # UBL format
                logger.info("Detected UBL format XRechnung")
                invoice_data = InvoiceParser._extract_from_ubl_xml(root, invoice_data)
            else:
                invoice_data.extraction_warnings.append(
                    f"Unknown XML namespace: {namespace}. Attempting generic extraction."
                )
                # Try generic extraction
                invoice_data = InvoiceParser._extract_from_generic_xml(root, invoice_data)

        except FileNotFoundError:
            invoice_data.extraction_errors.append(f"File not found: {xml_path}")
        except etree.XMLSyntaxError as e:
            invoice_data.extraction_errors.append(f"Invalid XML syntax: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing XRechnung XML {xml_path}: {e}")
            invoice_data.extraction_errors.append(f"XRechnung parsing error: {str(e)}")

        return invoice_data

    @staticmethod
    def _extract_from_facturx_dict(data: dict, invoice_data: InvoiceData) -> InvoiceData:
        """
        Extract invoice data from factur-x dictionary

        Args:
            data: Dictionary returned by factur-x
            invoice_data: InvoiceData object to populate

        Returns:
            Updated InvoiceData object
        """
        try:
            logger.info(f"Extracting data from factur-x dict with keys: {list(data.keys())}")

            # Invoice number - try multiple field names
            for field in ['invoice_number', 'number', 'InvoiceNumber', 'ID']:
                if field in data and data[field]:
                    invoice_data.invoice_number = str(data[field])
                    logger.info(f"Found invoice_number: {invoice_data.invoice_number}")
                    break

            # Invoice date - try multiple field names
            for field in ['date', 'invoice_date', 'IssueDate', 'issue_date']:
                if field in data and data[field]:
                    invoice_data.invoice_date = InvoiceParser._parse_date(data[field])
                    logger.info(f"Found invoice_date: {invoice_data.invoice_date}")
                    break

            # Due date - try multiple field names
            for field in ['due_date', 'DueDate', 'payment_due_date']:
                if field in data and data[field]:
                    invoice_data.due_date = InvoiceParser._parse_date(data[field])
                    logger.info(f"Found due_date: {invoice_data.due_date}")
                    break

            # Supplier information - try multiple structures
            seller = None
            for field in ['seller', 'Seller', 'supplier', 'AccountingSupplierParty']:
                if field in data:
                    seller = data[field]
                    break

            if seller and isinstance(seller, dict):
                # Name
                for field in ['name', 'Name', 'PartyName']:
                    if field in seller and seller[field]:
                        invoice_data.supplier_name = str(seller[field])
                        logger.info(f"Found supplier_name: {invoice_data.supplier_name}")
                        break

                # ID/VAT
                for field in ['vat', 'VAT', 'tax_id', 'TaxID', 'CompanyID']:
                    if field in seller and seller[field]:
                        invoice_data.supplier_id = str(seller[field])
                        logger.info(f"Found supplier_id: {invoice_data.supplier_id}")
                        break

            # Amounts - try multiple field names
            for field in ['amount_total', 'total_amount', 'TotalAmount', 'PayableAmount', 'GrandTotalAmount']:
                if field in data and data[field]:
                    invoice_data.amount_gross = InvoiceParser._parse_decimal(data[field])
                    logger.info(f"Found amount_gross: {invoice_data.amount_gross}")
                    break

            for field in ['amount_untaxed', 'net_amount', 'NetAmount', 'TaxExclusiveAmount', 'TaxBasisTotalAmount']:
                if field in data and data[field]:
                    invoice_data.amount_net = InvoiceParser._parse_decimal(data[field])
                    logger.info(f"Found amount_net: {invoice_data.amount_net}")
                    break

            # VAT amount
            for field in ['amount_tax', 'tax_amount', 'TaxAmount', 'TaxTotalAmount']:
                if field in data and data[field]:
                    invoice_data.amount_vat = InvoiceParser._parse_decimal(data[field])
                    logger.info(f"Found amount_vat: {invoice_data.amount_vat}")
                    break

            # Currency
            for field in ['currency', 'Currency', 'DocumentCurrencyCode', 'currency_code']:
                if field in data and data[field]:
                    invoice_data.currency = str(data[field])
                    logger.info(f"Found currency: {invoice_data.currency}")
                    break

            logger.info(f"Extraction complete. Extracted fields: invoice_number={invoice_data.invoice_number}, "
                       f"supplier_name={invoice_data.supplier_name}, amount_gross={invoice_data.amount_gross}")

        except Exception as e:
            logger.error(f"Error extracting from factur-x dict: {e}", exc_info=True)
            invoice_data.extraction_warnings.append(f"Partial extraction error: {str(e)}")

        return invoice_data

    @staticmethod
    def _extract_from_cii_xml(root: etree._Element, invoice_data: InvoiceData) -> InvoiceData:
        """
        Extract data from CII (Cross Industry Invoice) XML

        Args:
            root: XML root element
            invoice_data: InvoiceData object to populate

        Returns:
            Updated InvoiceData object
        """
        try:
            # Define namespace
            ns = {'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
                  'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
                  'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'}

            # Invoice number (ExchangedDocument is in rsm namespace, not ram!)
            invoice_no = root.xpath('//rsm:ExchangedDocument/ram:ID/text()', namespaces=ns)
            if invoice_no:
                invoice_data.invoice_number = invoice_no[0]
                logger.info(f"Extracted invoice_number: {invoice_data.invoice_number}")

            # Invoice date (ExchangedDocument is in rsm namespace, not ram!)
            invoice_date = root.xpath('//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString/text()', namespaces=ns)
            if invoice_date:
                invoice_data.invoice_date = InvoiceParser._parse_date(invoice_date[0])
                logger.info(f"Extracted invoice_date: {invoice_data.invoice_date}")

            # Supplier name
            seller_name = root.xpath('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:Name/text()', namespaces=ns)
            if seller_name:
                invoice_data.supplier_name = seller_name[0]

            # Supplier ID (VAT)
            seller_vat = root.xpath('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID/text()', namespaces=ns)
            if seller_vat:
                invoice_data.supplier_id = seller_vat[0]

            # Supplier contact email (DefinedTradeContact/EmailURIUniversalCommunication)
            seller_email = root.xpath('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID/text()', namespaces=ns)
            if seller_email:
                invoice_data.supplier_email = seller_email[0]

            # Supplier electronic address (URIUniversalCommunication)
            seller_electronic_address = root.xpath('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:URIUniversalCommunication/ram:URIID/text()', namespaces=ns)
            if seller_electronic_address:
                invoice_data.supplier_electronic_address = seller_electronic_address[0]

            # Amounts
            amount_gross = root.xpath('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount/text()', namespaces=ns)
            if amount_gross:
                invoice_data.amount_gross = InvoiceParser._parse_decimal(amount_gross[0])

            amount_net = root.xpath('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount/text()', namespaces=ns)
            if amount_net:
                invoice_data.amount_net = InvoiceParser._parse_decimal(amount_net[0])

            amount_vat = root.xpath('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount/text()', namespaces=ns)
            if amount_vat:
                invoice_data.amount_vat = InvoiceParser._parse_decimal(amount_vat[0])

            # Currency - try multiple locations
            currency = root.xpath('//ram:InvoiceCurrencyCode/text()', namespaces=ns)
            if not currency:
                currency = root.xpath('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount/@currencyID', namespaces=ns)
            if currency:
                invoice_data.currency = currency[0]
                logger.info(f"Extracted currency: {invoice_data.currency}")

            # Due date
            due_date = root.xpath('//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString/text()', namespaces=ns)
            if due_date:
                invoice_data.due_date = InvoiceParser._parse_date(due_date[0])
                logger.info(f"Extracted due_date: {invoice_data.due_date}")

        except Exception as e:
            logger.error(f"Error extracting from CII XML: {e}")
            invoice_data.extraction_warnings.append(f"CII extraction error: {str(e)}")

        return invoice_data

    @staticmethod
    def _extract_from_ubl_xml(root: etree._Element, invoice_data: InvoiceData) -> InvoiceData:
        """
        Extract data from UBL (Universal Business Language) XML

        Args:
            root: XML root element
            invoice_data: InvoiceData object to populate

        Returns:
            Updated InvoiceData object
        """
        try:
            # Define namespace
            ns = {'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                  'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}

            # Invoice number
            invoice_no = root.xpath('//cbc:ID/text()', namespaces=ns)
            if invoice_no:
                invoice_data.invoice_number = invoice_no[0]

            # Invoice date
            invoice_date = root.xpath('//cbc:IssueDate/text()', namespaces=ns)
            if invoice_date:
                invoice_data.invoice_date = InvoiceParser._parse_date(invoice_date[0])

            # Due date
            due_date = root.xpath('//cbc:DueDate/text()', namespaces=ns)
            if due_date:
                invoice_data.due_date = InvoiceParser._parse_date(due_date[0])

            # Supplier name
            seller_name = root.xpath('//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name/text()', namespaces=ns)
            if seller_name:
                invoice_data.supplier_name = seller_name[0]

            # Supplier ID (VAT)
            seller_vat = root.xpath('//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID/text()', namespaces=ns)
            if seller_vat:
                invoice_data.supplier_id = seller_vat[0]

            # Supplier contact email
            seller_email = root.xpath('//cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:ElectronicMail/text()', namespaces=ns)
            if seller_email:
                invoice_data.supplier_email = seller_email[0]

            # Supplier electronic address (EndpointID)
            seller_electronic_address = root.xpath('//cac:AccountingSupplierParty/cac:Party/cbc:EndpointID/text()', namespaces=ns)
            if seller_electronic_address:
                invoice_data.supplier_electronic_address = seller_electronic_address[0]

            # Amounts
            amount_gross = root.xpath('//cac:LegalMonetaryTotal/cbc:PayableAmount/text()', namespaces=ns)
            if amount_gross:
                invoice_data.amount_gross = InvoiceParser._parse_decimal(amount_gross[0])

            amount_net = root.xpath('//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount/text()', namespaces=ns)
            if amount_net:
                invoice_data.amount_net = InvoiceParser._parse_decimal(amount_net[0])

            amount_vat = root.xpath('//cac:TaxTotal/cbc:TaxAmount/text()', namespaces=ns)
            if amount_vat:
                invoice_data.amount_vat = InvoiceParser._parse_decimal(amount_vat[0])

            # Currency
            currency = root.xpath('//cbc:DocumentCurrencyCode/text()', namespaces=ns)
            if currency:
                invoice_data.currency = currency[0]

        except Exception as e:
            logger.error(f"Error extracting from UBL XML: {e}")
            invoice_data.extraction_warnings.append(f"UBL extraction error: {str(e)}")

        return invoice_data

    @staticmethod
    def _extract_from_generic_xml(root: etree._Element, invoice_data: InvoiceData) -> InvoiceData:
        """
        Attempt generic extraction from unknown XML format

        Args:
            root: XML root element
            invoice_data: InvoiceData object to populate

        Returns:
            Updated InvoiceData object
        """
        try:
            # Try to find common elements without namespace
            # This is a best-effort approach for unknown formats

            # Look for invoice number variations
            for xpath in ['//InvoiceNumber', '//ID', '//Number']:
                try:
                    result = root.xpath(xpath + '/text()')
                    if result:
                        invoice_data.invoice_number = result[0]
                        break
                except:
                    pass

            invoice_data.extraction_warnings.append(
                "Generic XML parsing used - results may be incomplete"
            )

        except Exception as e:
            logger.error(f"Error in generic XML extraction: {e}")
            invoice_data.extraction_errors.append(f"Generic extraction failed: {str(e)}")

        return invoice_data

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object
        Supports multiple formats: ISO 8601, YYYYMMDD, etc.
        """
        if not date_str:
            return None

        # Try various date formats
        formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%Y%m%d',             # 20240115
            '%d.%m.%Y',           # 15.01.2024
            '%Y-%m-%dT%H:%M:%S',  # ISO 8601 with time
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def _parse_decimal(value: any) -> Optional[Decimal]:
        """
        Parse value to Decimal
        """
        if value is None:
            return None

        try:
            if isinstance(value, Decimal):
                return value
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                # Remove spaces and convert comma to dot
                value = value.strip().replace(',', '.')
                return Decimal(value)
        except Exception as e:
            logger.warning(f"Could not parse decimal: {value} - {e}")

        return None
