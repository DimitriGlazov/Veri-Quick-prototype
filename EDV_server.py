# Importing necessary modules
import streamlit as st
import dropbox
import json
import re
from datetime import datetime
import qrcode
from io import BytesIO
import requests
import fitz  # PyMuPDF for better PDF text extraction

# Dropbox credentials
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Initialize Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

# Aadhaar and PAN regex patterns
AADHAAR_REGEX = r"\b\d{4} \d{4} \d{4}\b"
PAN_REGEX = r"\b[A-Z]{5}\d{4}[A-Z]{1}\b"

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

# Function to upload a file to Dropbox and get a public link
def upload_file_to_dropbox(file, filename):
    global dbx
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dropbox_path = f"/Veriquick/{timestamp}_{filename}"

    try:
        dbx.files_upload(file.getvalue(), dropbox_path)
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        return shared_link_metadata.url.replace("?dl=0", "?dl=1")

    except dropbox.exceptions.AuthError:
        
        if refresh_access_token():
            return upload_file_to_dropbox(file, filename)
        else:
            st.error("Failed to refresh access token. Please check your credentials.")
            return None
    except dropbox.exceptions.ApiError as e:
        st.error(f"Dropbox API error: {e}")
        return None

# Function to extract Aadhaar and PAN metadata from content
def extract_metadata_from_pdf(file_content, file_url):
    metadata = {"document_url": file_url, "document_type": "Other", "aadhaar_numbers": [], "pan_numbers": []}

    try:
        # Read PDF content using PyMuPDF
        pdf_document = fitz.open("pdf", file_content)
        text_content = ""
        for page in pdf_document:
            text_content += page.get_text()
        
        # Extract Aadhaar and PAN numbers from text
        aadhaar_numbers = re.findall(AADHAAR_REGEX, text_content)
        pan_numbers = re.findall(PAN_REGEX, text_content)

        # Update metadata based on detected document types
        if aadhaar_numbers:
            metadata["document_type"] = "Aadhaar"
            metadata["aadhaar_numbers"] = aadhaar_numbers
        elif pan_numbers:
            metadata["document_type"] = "PAN"
            metadata["pan_numbers"] = pan_numbers

    except Exception as e:
        st.error(f"Error extracting metadata: {e}")

    return metadata

# Function to generate QR code from metadata
def generate_qr_code_with_metadata(files_metadata):
    qr_data = json.dumps({"files": files_metadata})
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    return img

# Main Streamlit App
st.title("Veriquick ✅")
st.write(" Verification made paperless.")

uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", accept_multiple_files=True)

if uploaded_files:
    files_metadata = []

    for uploaded_file in uploaded_files:
        file_content = BytesIO(uploaded_file.read())
        file_url = upload_file_to_dropbox(file_content, uploaded_file.name)
        
        if file_url:
            metadata = extract_metadata_from_pdf(file_content, file_url)
            files_metadata.append(metadata)

    # Generate and display QR code if files are uploaded
    if files_metadata:
        qr_image = generate_qr_code_with_metadata(files_metadata)
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        st.image(qr_buffer, caption="QR Code with Document Metadata", use_column_width=True)
        st.download_button(label="Download QR Code", data=qr_buffer, file_name="document_metadata_qr.png", mime="image/png")
        st.json(files_metadata)  # Display metadata as JSON for reference
