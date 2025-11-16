import os
import logging
from .compressor import FileCompressor
from .chunker import DataChunker
from .qr_generator import QRCodeGenerator
from .video_writer import VideoWriter

logger = logging.getLogger(__name__)


class QRVideoGenerator:
    def __init__(self, qr_version=40, qr_size=400, fps=25):
        self.compressor = FileCompressor()
        self.chunker = DataChunker()
        self.qr_generator = QRCodeGenerator(version=qr_version, qr_size=qr_size)
        self.fps = fps
        self.qr_size = qr_size
    
    def generate(self, input_file, output_video):
        logger.info(f"Starting QR video generation: {input_file}")
        
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            raise FileNotFoundError(input_file)
        
        zip_file = self.compressor.create_zip(input_file)
        
        try:
            with open(zip_file, 'rb') as f:
                zip_data = f.read()
            
            compressed_data = self.compressor.compress_data(zip_data)
            
            num_chunks = self.chunker.calculate_chunks(len(compressed_data))
            
            qr_images = []
            for i in range(num_chunks):
                chunk = self.chunker.create_chunk(compressed_data, i, num_chunks)
                qr_image = self.qr_generator.generate_qr_code(chunk)
                qr_images.append(qr_image)
            
            logger.info(f"Generated {len(qr_images)} QR codes")
            
            frame_size = (self.qr_size + 20, self.qr_size + 20)
            video_writer = VideoWriter(output_video, fps=self.fps, frame_size=frame_size)
            video_writer.open()
            
            for idx, img in enumerate(qr_images):
                video_writer.write_frame(img)
                if (idx + 1) % 10 == 0:
                    logger.info(f"Written {idx+1}/{len(qr_images)} frames")
            
            video_writer.close()
            
            video_duration = len(qr_images) / self.fps
            logger.info(f"Video duration: {video_duration:.2f} seconds")
            logger.info(f"Total frames: {len(qr_images)}")
            
            self._log_summary(input_file, len(compressed_data), len(qr_images), output_video)
            
        finally:
            if os.path.exists(zip_file):
                os.remove(zip_file)
                logger.info("Cleaned up temporary ZIP file")
    
    def _log_summary(self, input_file, compressed_size, num_qrs, output_video):
        input_size = os.path.getsize(input_file)
        total_compression = (1 - compressed_size/input_size) * 100
        
        logger.info("="*60)
        logger.info("SUMMARY:")
        logger.info(f"  Input file: {os.path.basename(input_file)}")
        logger.info(f"  Original size: {input_size:,} bytes ({input_size/1024:.2f} KB)")
        logger.info(f"  Compressed size: {compressed_size:,} bytes ({compressed_size/1024:.2f} KB)")
        logger.info(f"  Total compression: {total_compression:.2f}%")
        logger.info(f"  QR codes: {num_qrs}")
        logger.info(f"  Output video: {output_video}")
        logger.info("="*60)


