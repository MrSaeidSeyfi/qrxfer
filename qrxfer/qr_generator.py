import qrcode
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    def __init__(self, version=40, qr_size=400, border_color=(0, 255, 0)):
        self.version = version
        self.qr_size = qr_size
        self.border_color = border_color
        self.border_width = 10
    
    def generate_qr_code(self, data):
        logger.info(f"Generating QR code (version {self.version})")
        
        qr = qrcode.QRCode(
            version=self.version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        logger.info(f"QR version used: {qr.version}")
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((self.qr_size, self.qr_size), Image.Resampling.LANCZOS)
        
        bordered_size = self.qr_size + (2 * self.border_width)
        bordered = Image.new('RGB', (bordered_size, bordered_size), self.border_color)
        bordered.paste(img.convert('RGB'), (self.border_width, self.border_width))
        
        return np.array(bordered)


