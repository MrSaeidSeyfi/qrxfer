import os
import zlib
import zipfile
import tempfile
import logging

logger = logging.getLogger(__name__)


class FileCompressor:
    def __init__(self, compression_level=9):
        self.compression_level = compression_level
        
    def create_zip(self, input_file):
        logger.info(f"Creating ZIP from: {input_file}")
        zip_path = tempfile.mktemp(suffix='.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
            arcname = os.path.basename(input_file)
            zipf.write(input_file, arcname=arcname)
            logger.info(f"Added '{arcname}' to ZIP")
        
        zip_size = os.path.getsize(zip_path)
        original_size = os.path.getsize(input_file)
        compression_ratio = (1 - zip_size/original_size) * 100
        logger.info(f"ZIP size: {zip_size:,} bytes, compression: {compression_ratio:.2f}%")
        
        return zip_path
    
    def compress_data(self, data):
        logger.info(f"Compressing {len(data):,} bytes with zlib")
        compressed = zlib.compress(data, level=self.compression_level)
        compression_ratio = (1 - len(compressed)/len(data)) * 100
        logger.info(f"Compressed to {len(compressed):,} bytes, ratio: {compression_ratio:.2f}%")
        return compressed

