# Importing necessary modules
import cv2
import pyzbar.pyzbar as pyzbar
import webbrowser
import pygame
import sys
import json
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QTimer
import requests

# Initialize pygame mixer
pygame.mixer.init()

# Paths to sounds
SUCCESS_SOUND = "D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\verfication unsuccessful manual checking neede.mp3"
AADHAAR_DETECTED_SOUND = "D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\Aadhar detected.mp3"
class QRScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)  # Width
        self.cap.set(4, 720)   # Height
        self.browser_opened = False
        self.qr_data = None

        # Timer to update the video feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Frame rate control

    def initUI(self):
        self.setWindowTitle("Veriquick - Document Scanner")
        self.setWindowIcon(QIcon("D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\qricon.ico"))
        
        # Set up layout and video display label
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.show()

    def update_frame(self):
        success, frame = self.cap.read()
        if not success:
            print("Error reading frame from camera.")
            return

        # Decode QR code from frame
        decoded_objs = pyzbar.decode(frame)
        if decoded_objs:
            for obj in decoded_objs:
                data = obj.data.decode('utf-8')
                print(f"Decoded QR Code Data: {data}")
                x, y, w, h = obj.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 250, 0), 2)

                # Process QR data if it's a new scan
                if not self.browser_opened and (self.qr_data is None or self.qr_data != data):
                    self.qr_data = data
                    document_metadata = self.process_qr_data(data)

                    if document_metadata:
                        for doc in document_metadata["files"]:
                            doc_type = doc.get("document_type", "Unknown")
                            doc_url = doc.get("document_url", "")
                            aadhaar_numbers = doc.get("aadhaar_numbers", [])

                            # Check if document type is "Aadhaar" and contains Aadhaar numbers
                            if doc_type == "Aadhaar" and aadhaar_numbers:
                                print("Aadhaar detected. Opening document...")
                                self.play_sound(AADHAAR_DETECTED_SOUND)
                                webbrowser.open(doc_url)
                                self.browser_opened = True
                            else:
                                print(f"{doc_type} document needs manual verification.")
                                webbrowser.open(doc_url)
                                self.browser_opened = True

                        # Play success sound after processing all documents
                        self.play_sound(SUCCESS_SOUND)

                    QTimer.singleShot(5000, self.reset_browser_flag)  # Reset after 5 seconds
        else:
            self.qr_data = None

        # Convert the frame to RGB and display it in the PyQt5 window
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def process_qr_data(self, qr_data):
        try:
            return json.loads(qr_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding QR data: {e}")
            return None

    def play_sound(self, sound_path):
        """Play sound at specified path with error handling."""
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            print(f"Played sound: {sound_path}")
        except pygame.error as e:
            print(f"Error playing sound {sound_path}: {e}")

    def reset_browser_flag(self):
        """Reset browser flag to allow future scans."""
        self.browser_opened = False

    def closeEvent(self, event):
        # Release the camera and close OpenCV window
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scanner = QRScannerApp()
    sys.exit(app.exec_())
