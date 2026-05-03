from abc import ABC, abstractmethod
from PIL import Image
import mimetypes

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


class MetadataExtractorFactory:
    @staticmethod
    def get_extractor(filepath):
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type:
            if mime_type.startswith('image'):
                return ImageMetadataExtractor()

def extract_metadata(filepath):
    extractor = MetadataExtractorFactory.get_extractor(filepath)
    return extractor.extract(filepath)