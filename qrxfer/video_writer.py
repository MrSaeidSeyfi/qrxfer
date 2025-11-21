import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VideoWriter:
    def __init__(self, output_path, fps=25, frame_size=(420, 420), codec_priority=("H264", "avc1", "XVID", "MP4V")):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.writer = None
        self.codec_priority = codec_priority
        self.active_codec = None     
    
    def open(self):
        logger.info(f"Opening video writer: {self.output_path}")
        for codec in self.codec_priority:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, self.frame_size, True)
            if writer.isOpened():
                self.writer = writer
                self.active_codec = codec
                break
        
        if self.writer and hasattr(cv2, "VIDEOWRITER_PROP_QUALITY"):
            self.writer.set(cv2.VIDEOWRITER_PROP_QUALITY, 100)
        
        if not self.writer or not self.writer.isOpened():
            logger.error("Failed to open video writer")
            raise IOError("Could not open video writer")
        
        logger.info(f"Video writer opened: {self.fps} fps, size {self.frame_size}, codec {self.active_codec}")
    
    def write_frame(self, frame_rgb):
        if self.writer is None:
            raise RuntimeError("Video writer not opened")
        
        frame_bgr = cv2.cvtColor(frame_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)
        self.writer.write(frame_bgr)
    
    def close(self):
        if self.writer:
            self.writer.release()
            logger.info(f"Video saved: {self.output_path}")



