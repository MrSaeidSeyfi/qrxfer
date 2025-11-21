import os
import logging
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .compressor import FileCompressor
from .chunker import DataChunker
from .qr_generator import QRCodeGenerator
from .video_writer import VideoWriter

logger = logging.getLogger(__name__)


def _generate_qr_worker(args):
    chunk_data, chunk_index, total_chunks, qr_version, qr_size = args
    qr_gen = QRCodeGenerator(version=qr_version, qr_size=qr_size)
    qr_image = qr_gen.generate_qr_code(chunk_data)
    logger.info(f"Generated QR code {chunk_index+1}/{total_chunks}")
    return chunk_index, qr_image

class QRVideoGenerator:
    def __init__(self, qr_version=40, qr_size=400, fps=25, num_processes=4):
        self.compressor = FileCompressor()
        self.chunker = DataChunker()
        self.qr_generator = QRCodeGenerator(version=qr_version, qr_size=qr_size)
        self.fps = fps
        self.qr_size = qr_size
        self.num_processes = num_processes
    
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
            
            chunks_data = []
            for i in range(num_chunks):
                chunk = self.chunker.create_chunk(compressed_data, i, num_chunks)
                chunks_data.append((chunk, i, num_chunks, self.qr_generator.version, self.qr_size))
            
            logger.info(f"Generating {num_chunks} QR codes using {self.num_processes} processes")
            
            qr_images = [None] * num_chunks
            with Pool(processes=self.num_processes) as pool:
                results = pool.map(_generate_qr_worker, chunks_data)
                for chunk_index, qr_image in results:
                    qr_images[chunk_index] = qr_image
            
            logger.info(f"Generated {len(qr_images)} QR codes")
            
            frame_size = (self.qr_size + 20, self.qr_size + 20)
            video_writer = VideoWriter(output_video, fps=self.fps, frame_size=frame_size)
            video_writer.open()
            
            countdown_frames = int(self.fps * 3)
            logger.info(f"Adding {countdown_frames} countdown frames (3 seconds)")
            
            for i in range(countdown_frames):
                countdown_value = 3 - ((i + 1) / self.fps)
                countdown_frame = self._create_countdown_frame(frame_size, countdown_value)
                video_writer.write_frame(countdown_frame)
            
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
    
    def _create_countdown_frame(self, frame_size, countdown_value):
        img = Image.new('RGB', frame_size, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            except:
                font = ImageFont.load_default()
        
        if countdown_value >= 2:
            text = "3"
        elif countdown_value >= 1:
            text = "2"
        elif countdown_value > 0:
            text = "1"
        else:
            text = "GO"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (frame_size[0] - text_width) // 2
        y = (frame_size[1] - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        return np.array(img)
    
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


