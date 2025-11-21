import struct
import zlib
import logging

logger = logging.getLogger(__name__)


class DataChunker:
    def __init__(self, max_qr_capacity=1260, header_size=8, checksum_size=4):
        self.max_qr_capacity = max_qr_capacity
        self.header_size = header_size
        self.checksum_size = checksum_size
        self.chunk_size = max_qr_capacity - header_size - checksum_size
    
    def calculate_chunks(self, data_size):
        num_chunks = (data_size + self.chunk_size - 1) // self.chunk_size
        logger.info(f"Data size: {data_size:,} bytes")
        logger.info(f"Chunk size: {self.chunk_size} bytes")
        logger.info(f"Number of chunks: {num_chunks}")
        return num_chunks
    
    def create_chunk(self, data, chunk_index, total_chunks):
        start = chunk_index * self.chunk_size
        end = min(start + self.chunk_size, len(data))
        chunk_data = data[start:end]
        
        header = struct.pack('<II', total_chunks, chunk_index)
        crc = struct.pack('<I', zlib.crc32(chunk_data) & 0xffffffff)
        full_chunk = header + chunk_data + crc
        
        logger.info(f"Chunk {chunk_index+1}/{total_chunks}: {len(chunk_data)} bytes")
        
        if len(full_chunk) > self.max_qr_capacity:
            logger.error(f"Chunk too large: {len(full_chunk)} > {self.max_qr_capacity}")
            raise ValueError("Chunk exceeds maximum QR capacity")
        
        return full_chunk



