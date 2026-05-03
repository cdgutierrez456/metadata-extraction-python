import re
import docx
import mimetypes
from PIL import Image
from abc import ABC, abstractmethod
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

class MetadataExtractor(ABC):
    @abstractmethod
    def extract(self, filepath):
        pass


class ImageMetadataExtractor(MetadataExtractor):
    def extract(self, filepath):
        with Image.open(filepath) as img:
            if img.format in ['JPG', 'JPEG']:
                exif = img.getexif()
                if exif:
                    return {Image.ExifTags.TAGS.get(key, key): value
                            for key, value in exif.items() if key in Image.ExifTags.TAGS}
                else:
                    return {'Error': 'No EXIF metadata found'}
            elif img.format in ['PNG']:
                if img.info:
                    return img.info
                else:
                    return { 'Error': 'No metadata found' }
            else:
                return {'Error': 'unsupported image format'}

class PdfMetadataExtractor(MetadataExtractor):
    def extract(self, filepath):
        metadata = {}
        with open(filepath, 'rb') as f:
            parser = PDFParser(f)
            doc = PDFDocument(parser)
            if doc.info:
                for info in doc.info:
                    for key, value in info.items():
                        # Verificamos si el valor de la clave son bytes
                        if isinstance(value, bytes):
                            try:
                                # Intentar decodificarlo en UTF-16BE
                                decode_value = value.decode('utf-16be')
                            except UnicodeDecodeError:
                                # Intentar decodificarlo en UTF-8
                                decode_value = value.decode('utf-8', errors='ignore')
                        else:
                            decode_value = value

                        metadata[key] = decode_value
            # procesamos el texto del pdf para obtener otros datos de interes
            text = extract_text(filepath)
            metadata["Emails"] = self._extract_emails(text)
        return metadata

    def _extract_emails(self, text):
        email_regex = r'[a-zA-Z0-0._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_regex, text)

class DocxMetadataExtractor(MetadataExtractor):
    def extract(self, filepath):
        doc = docx.Document(filepath)
        prop = doc.core_properties
        attributes = [
            'author', 'category', 'comments', 'content_status',
            'created', 'identifier', 'keywords', 'last_modified_by',
            'language', 'modified', 'subject', 'title', 'version'
        ]
        metadata = {attr: getattr(prop, attr, None) for attr in attributes}
        return metadata

class MetadataExtractorFactory:
    @staticmethod
    def get_extractor(filepath):
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type:
            if mime_type.startswith('image'):
                return ImageMetadataExtractor()
            if mime_type == 'application/pdf':
                return PdfMetadataExtractor()
            if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return DocxMetadataExtractor()
        raise ValueError('Unsupported file type')

def extract_metadata(filepath):
    extractor = MetadataExtractorFactory.get_extractor(filepath)
    return extractor.extract(filepath)