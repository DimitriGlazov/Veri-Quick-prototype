import streamlit as st
import dropbox
import qrcode
from PIL import Image
import io
import json
import requests
from requests.auth import HTTPBasicAuth

# Streamlit app configuration
st.set_page_config(page_title=" Veri quick ✅ ©️")
st.header("Veri quick©️ ✅ ")
st.subheader(" Making paperless and qucik verifications ")

# Dropbox API configuration
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Refresh token if needed
def refresh_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"
    refresh_params = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    
    response = requests.post(token_url, data=refresh_params, auth=auth)
    
    if response.status_code == 200:
        new_access_token = response.json().get("access_token")
        # Update global ACCESS_TOKEN with the new token
        global ACCESS_TOKEN
        ACCESS_TOKEN = new_access_token
        st.secrets["dropbox"]["access_token"] = new_access_token  # Update Streamlit secrets dynamically
    else:
        st.error("Failed to refresh Dropbox access token. Please check your credentials.")

# Initialize Dropbox client with refreshed token if needed
def init_dropbox():
    try:
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        dbx.users_get_current_account()  # Check if token is valid
        return dbx
    except dropbox.exceptions.AuthError:
        # If token is expired, refresh and retry
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
            dbx.files_upload(file.getbuffer(), file_path)
            shared_link = dbx.sharing_create_shared_link_with_settings(file_path).url
            doc_type = identify_document_type(file.name)

            if doc_type:
                files_metadata.append({
                    "document_url": shared_link,
                    "document_type": doc_type
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

# Document type identification based on filename
def identify_document_type(filename):
    if "aadhar" in filename.lower():
        return "Aadhaar"
    elif "pan" in filename.lower():
        return "PAN"
    elif "marksheet" in filename.lower():
        return "Marksheet"
    else:
        return None

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
