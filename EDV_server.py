import cv2
import pyzbar.pyzbar as pyzbar
import webbrowser
import json
import requests
from PyPDF2 import PdfFileReader
import io
import re
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class QRScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)  # Width
        self.cap.set(4, 720)   # Height
        self.qr_data = None

        # Timer to update the video feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(2)

    def initUI(self):
        # Set up the window
        self.setWindowTitle("EDV QR Scanner")
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.show()

    def update_frame(self):
        success, image = self.cap.read()
        if not success:
            return

        # Decode the QR code in the image
        decoded_objs = pyzbar.decode(image)

        if decoded_objs:
            for obj in decoded_objs:
                data = obj.data.decode('utf-8')
                metadata = json.loads(data)

                document_url = metadata.get("document_url")
                document_type = metadata.get("document_type")

                if document_type == "Aadhaar":
                    # Fetch and verify Aadhaar document
                    self.verify_aadhaar(document_url)
                else:
                    # Open non-Aadhaar document in a browser
                    webbrowser.open(document_url)

                break  # Stop after processing the first QR code

        # Convert the image to RGB and display it
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convert_to_qt_format)
        self.image_label.setPixmap(pixmap)

    def verify_aadhaar(self, document_url):
        response = requests.get(document_url)
        document_content = response.content

        # Example assumes document is a PDF containing text
        pdf_reader = PdfFileReader(io.BytesIO(document_content))
        text = ""
        for page_num in range(pdf_reader.numPages):
            text += pdf_reader.getPage(page_num).extractText()

        # Extract Aadhaar number using regex
        aadhaar_match = re.search(r'\d{4}\s\d{4}\s\d{4}', text)
        if aadhaar_match:
            aadhaar_number = aadhaar_match.group(0)
            if self.validate_aadhaar(aadhaar_number):
                print(f"Valid Aadhaar: {aadhaar_number}")
            else:
                print(f"Invalid Aadhaar: {aadhaar_number}")
        else:
            print("No Aadhaar number found in the document.")

    def validate_aadhaar(self, aadhaar_number):
        # Simple validation logic (e.g., checksum validation) or integrate with a government API
        # Placeholder logic for now
        return True  # For demo purposes

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qr_scanner_app = QRScannerApp()
    sys.exit(app.exec_())
