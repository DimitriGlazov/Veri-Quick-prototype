import streamlit as st
import dropbox
import qrcode
from PIL import Image
import io
import json
import requests
from requests.auth import HTTPBasicAuth
import re

# Streamlit app configuration
st.set_page_config(page_title="EDV Server - Document Upload and QR Generation")
st.header("EDV Document Uploader")
st.subheader("Upload and verify documents with QR code generation")

# Dropbox API configuration
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Refresh token if needed
def refresh_access_token():
    global ACCESS_TOKEN  # Update in memory only
    token_url = "https://api.dropbox.com/oauth2/token"
    refresh_params = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    
    response = requests.post(token_url, data=refresh_params, auth=auth)
    
    if response.status_code == 200:
        new_access_token = response.json().get("access_token")
        ACCESS_TOKEN = new_access_token  # Update the token only in memory
    else:
        st.error("Failed to refresh Dropbox access token. Please check your credentials.")

# Initialize Dropbox client with refreshed token if needed
def init_dropbox():
    try:
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        dbx.users_get_current_account()  # Check if token is valid
        return dbx
    except dropbox.exceptions.AuthError:
        st.warning("Access token expired. Refreshing...")
        refresh_access_token()
        return dropbox.Dropbox(ACCESS_TOKEN)

dbx = init_dropbox()

# Upload files to Dropbox and generate QR metadata
def upload_and_generate_metadata(uploaded_files):
    files_metadata = []

    for file in uploaded_files:
        try:
            file_path = f"/{file.name}"
            # Convert to binary before uploading to Dropbox
            file_binary = io.BytesIO(file.read())  # Converts memoryview to BytesIO
            
            dbx.files_upload(file_binary.getvalue(), file_path)  # Upload as binary content
            shared_link = dbx.sharing_create_shared_link_with_settings(file_path).url
            file_type = identify_document_type(file)

            files_metadata.append({
                "document_url": shared_link,
                "document_type": file_type
            })
        except Exception as e:
            st.error(f"Error uploading {file.name}: {e}")

    if files_metadata:
        qr_metadata = json.dumps({"files": files_metadata})
        qr_code_image = generate_qr_code(qr_metadata)
        qr_code_bytes = pil_image_to_bytes(qr_code_image)

        # Display and download QR code
        st.image(qr_code_image, caption="QR Code for Uploaded Documents")
        st.download_button("Download QR Code", data=qr_code_bytes, file_name="qr_code.png", mime="image/png")

# Document type identification based on file content
def identify_document_type(file):
    file.seek(0)  # Reset file pointer to the beginning
    content = file.read().decode('utf-8', errors='ignore')  # Decode content as text

    # Check for keywords for Aadhaar, PAN, and Marksheet
    if re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", content):  # PAN format
        return "PAN"
    elif re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", content):  # Aadhaar format
        return "Aadhaar"
    elif re.search(r"\b(Board\s+Marks|CBSE|ICSE|Class\s+\d+)", content, re.IGNORECASE):  # Marks related words
        return "Marksheet"
    else:
        return "Unknown"

# QR code generation
def generate_qr_code(data):
    qr = qrcode.make(data)
    return qr

# Convert PIL image to bytes
def pil_image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# Main upload and processing
uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True)

if uploaded_files:
    upload_and_generate_metadata(uploaded_files)
