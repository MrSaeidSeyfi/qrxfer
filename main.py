import sys
import logging
from qrxfer.generator import QRVideoGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <input_file> [output_video]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_video = sys.argv[2] if len(sys.argv) > 2 else "compressed_qr_video.mp4"
    
    generator = QRVideoGenerator(qr_version=40, qr_size=400, fps=25)
    generator.generate(input_file, output_video)
    
    logger.info("Done!")


if __name__ == "__main__":
    main()


