import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VideoWriter:
    def __init__(self, output_path, fps=25, frame_size=(420, 420)):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.writer = None
    
    def open(self):
        logger.info(f"Opening video writer: {self.output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, self.frame_size)
        
        if not self.writer.isOpened():
            logger.error("Failed to open video writer")
            raise IOError("Could not open video writer")
        
        logger.info(f"Video writer opened: {self.fps} fps, size {self.frame_size}")
    
    def write_frame(self, frame_rgb):
        if self.writer is None:
            raise RuntimeError("Video writer not opened")
        
        frame_bgr = cv2.cvtColor(frame_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)
        self.writer.write(frame_bgr)
    
    def close(self):
        if self.writer:
            self.writer.release()
            logger.info(f"Video saved: {self.output_path}")


