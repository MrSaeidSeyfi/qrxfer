import qrcode
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    def __init__(self, version=8, qr_size=1000, border_color=(0, 255, 0), border_width=20):
        self.version = version
        self.qr_size = qr_size
        self.border_color = border_color
        self.border_width = border_width
    
    def generate_qr_code(self, data):
        logger.info(f"Generating QR code (version {self.version})")
        
        modules_count = (self.version * 4) + 17
        border_modules = 4
        target_modules = modules_count + (border_modules * 2)
        box_size = max(2, self.qr_size // target_modules)
        
        qr = qrcode.QRCode(
            version=self.version,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border_modules,
        )
        
        qr.add_data(data)
        qr.make(fit=False)
        
        logger.info(f"QR version used: {qr.version}")
        
        img = qr.make_image(fill_color=(0, 0, 0), back_color=(255, 255, 255)).convert('RGB')
        
        # Resize/paste if necessary
        if img.size[0] != self.qr_size or img.size[1] != self.qr_size:
            canvas = Image.new('RGB', (self.qr_size, self.qr_size), (255, 255, 255))
            offset = (
                (self.qr_size - img.size[0]) // 2,
                (self.qr_size - img.size[1]) // 2,
            )
            canvas.paste(img, offset)
            img = canvas
        
        bordered_size = self.qr_size + (2 * self.border_width)
        bordered = Image.new('RGB', (bordered_size, bordered_size), self.border_color)
        bordered.paste(img, (self.border_width, self.border_width))
        
        return np.array(bordered)


