# Importing necessary modules
import streamlit as st
import dropbox
import qrcode
from PIL import Image
import json
import io
import requests
import re
from datetime import datetime

# Homepage setup
st.set_page_config(page_title="🗄️ Veriquick File Uploader")
st.header("Veriquick ✅")
st.subheader("Upload files to store and retrieve Dropbox links and QR codes")

# Get secrets from Streamlit secrets management
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Initialize Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

# Function to refresh access token
def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN, dbx
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
        st.error(f"Failed to refresh access token: {response.json()}")
        return False

# Function to upload a file to Dropbox and get the link
def upload_to_dropbox(uploadedfile, filename):
    global dbx
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = f"/Veriquick/{unique_filename}"

    try:
        dbx.files_upload(uploadedfile.getbuffer().tobytes(), file_path)

        # Revoke any existing shared links and create a new one
        existing_links = dbx.sharing_list_shared_links(file_path).links
        for link in existing_links:
            dbx.sharing_revoke_shared_link(link.url)

        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        file_link = shared_link_metadata.url.replace('?dl=0', '?dl=1')
        return file_link

    except dropbox.exceptions.AuthError:
        st.warning("Access token expired. Refreshing token...")
        if refresh_access_token():
            return upload_to_dropbox(uploadedfile, filename)
        else:
            st.error("Failed to refresh access token. Please check your credentials.")
            return None
    except dropbox.exceptions.ApiError as e:
        st.error(f"Dropbox API error: {e}")
        return None

# Function to generate QR code with metadata
def generate_qr_code_with_metadata(files_metadata):
    metadata = {"files": files_metadata}
    qr_data = json.dumps(metadata)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    return img

# Function to convert PIL Image to bytes
def pil_image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# Function to identify document type and extract Aadhaar or PAN details
def identify_document_type_and_extract(content):
    aadhaar_numbers = re.findall(r"\b\d{4}\s\d{4}\s\d{4}\b", content)
    pan_numbers = re.findall(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", content)

    document_type = "Other"
    metadata = {
        "aadhaar_numbers": [],
        "pan_numbers": []
    }

    if aadhaar_numbers:
        document_type = "Aadhaar"
        metadata["aadhaar_numbers"] = aadhaar_numbers
    if pan_numbers:
        document_type = "PAN" if document_type == "Other" else "Aadhaar & PAN"
        metadata["pan_numbers"] = pan_numbers
    
    return document_type, metadata

# Upload section
uploaded_files = st.file_uploader("Upload multiple documents (Aadhaar, PAN, etc.)", type=['pdf'], accept_multiple_files=True)

if uploaded_files:
    files_metadata = []
    
    for uploaded_file in uploaded_files:
        try:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
        except Exception:
            content = ""
        
        document_type, extracted_metadata = identify_document_type_and_extract(content)
        file_link = upload_to_dropbox(uploaded_file, uploaded_file.name)
        
        if file_link:
            files_metadata.append({
                "document_url": file_link,
                "document_type": document_type,
                "aadhaar_numbers": extracted_metadata["aadhaar_numbers"],
                "pan_numbers": extracted_metadata["pan_numbers"]
            })
    
    if files_metadata:
        qr_image = generate_qr_code_with_metadata(files_metadata)
        qr_image_bytes = pil_image_to_bytes(qr_image)
        
        st.image(qr_image_bytes, caption="QR code with metadata for uploaded files")
        st.download_button(label="Download QR code", data=qr_image_bytes, file_name="qr_code.png", mime="image/png")
