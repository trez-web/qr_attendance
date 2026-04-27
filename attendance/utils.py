import json
import qrcode
from io import BytesIO
from django.conf import settings
import os

def generate_meeting_qr(meeting):
    """
    Generate ONE QR per meeting encoding meeting_id + secure token.
    Format: {"meeting_id": "...", "token": "<uuid>"}
    """
    data = json.dumps({"meeting_id": str(meeting.id), "token": str(meeting.qr_token)})

    qr = qrcode.QRCode(version=1, box_size=12, border=4,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    file_name = f"meeting_qr_{meeting.id}.png"
    qr_folder = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
    os.makedirs(qr_folder, exist_ok=True)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    with open(os.path.join(qr_folder, file_name), 'wb') as f:
        f.write(buffer.getvalue())

    return f"{settings.MEDIA_URL}qrcodes/{file_name}"
