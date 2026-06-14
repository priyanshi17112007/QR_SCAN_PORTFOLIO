import os
import qrcode
from PIL import Image

class QRService:
    @staticmethod
    def generate_profile_qr(profile_url: str, output_path: str) -> str:
        # Create output directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(profile_url)
        qr.make(fit=True)

        # Slate gray fill color to look elegant and scan on various readers
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        img.save(output_path)
        return output_path

qr_service = QRService()