"""
Creating a web Server to make sure the EDV's function 
Process:
1. File upload condition  
2. Data storage and execution with the links 
3. Retrieve the file link in the QR format to make the application redirect 
to the created link 
"""

# Importing necessary modules
import streamlit as st
import dropbox
import qrcode
from PIL import Image
import json
import io
import re
import requests
from PyPDF2 import PdfReader

# Homepage setup
st.set_page_config(page_title=" 🗄️ Veriquick Document Uploader")
st.header("Veriquick ✅")
st.subheader("Upload documents to store, retrieve Dropbox links, and generate QR codes with metadata")

# Dropbox configuration from Streamlit secrets
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Initialize Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

# Function to refresh access token
def refresh_access_token():
    global ACCESS_TOKEN, dbx
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        ACCESS_TOKEN = response.json().get("access_token")
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        return True
    else:
        st.error("Failed to refresh access token.")
        return False

# Function to upload file to Dropbox
def upload_to_dropbox(uploadedfile, filename):
    global dbx
    try:
        file_path = f"/Veriquick/{filename}"
        dbx.files_upload(uploadedfile.getbuffer().tobytes(), file_path)
        shared_link = dbx.sharing_create_shared_link_with_settings(file_path).url.replace("?dl=0", "?dl=1")
        return shared_link
    except dropbox.exceptions.AuthError:
        if refresh_access_token():
            return upload_to_dropbox(uploadedfile, filename)
        else:
            st.error("Failed to refresh access token.")
            return None

# Function to detect Aadhaar numbers in a PDF
def extract_aadhaar_numbers(file):
    pdf_reader = PdfReader(file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text() or ""

    aadhaar_pattern = r"\b\d{4}\s\d{4}\s\d{4}\b"
    aadhaar_numbers = re.findall(aadhaar_pattern, full_text)
    return list(set(aadhaar_numbers)) if aadhaar_numbers else []

# Function to generate QR code with metadata
def generate_qr_code_with_metadata(files_metadata):
    qr_data = json.dumps({"files": files_metadata})
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    return img

# Convert PIL Image to bytes
def pil_image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# Upload section
uploaded_files = st.file_uploader("Upload multiple documents (Aadhaar, PAN, etc.)", type=["pdf"], accept_multiple_files=True)

if uploaded_files is not None:
    files_metadata = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        document_type = st.selectbox(f"Select document type for {file_name}", ["Aadhaar", "PAN", "Passport", "Other"])

        # Upload file to Dropbox
        file_link = upload_to_dropbox(uploaded_file, file_name)
        if file_link:
            metadata_entry = {"document_url": file_link, "document_type": document_type}
            
            # Aadhaar detection for document type Aadhaar
            if document_type == "Aadhaar":
                aadhaar_numbers = extract_aadhaar_numbers(uploaded_file)
                metadata_entry["aadhaar_numbers"] = aadhaar_numbers

            files_metadata.append(metadata_entry)

    if files_metadata:
        qr_image = generate_qr_code_with_metadata(files_metadata)
        qr_image_bytes = pil_image_to_bytes(qr_image)

        st.image(qr_image_bytes, caption="QR code with metadata for uploaded files")
        st.download_button(label="Download QR code", data=qr_image_bytes, file_name="qr_code.png", mime="image/png")
