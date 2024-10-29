# Importing necessary modules
import streamlit as st
import dropbox
import qrcode
from PIL import Image
import json
import io
import requests
import PyPDF2  # Importing PyPDF2 to read PDF files
import re  # For regex operations

# Homepage setup
st.set_page_config(page_title=" 🗄️ EDV file uploader")
st.header(" Veriquick ✅")
st.subheader('Upload files to store and retrieve Dropbox links and QR codes')

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
        REFRESH_TOKEN = response.json().get("refresh_token")
        dbx = dropbox.Dropbox(ACCESS_TOKEN)
        return True
    else:
        st.error(f"Failed to refresh access token: {response.json()}")
        return False

# Function to upload a file to Dropbox and get the link
def upload_to_dropbox(uploadedfile, filename):
    global dbx
    try:
        file_path = f"/EDV/{filename}"
        dbx.files_upload(uploadedfile.getbuffer().tobytes(), file_path)
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        file_link = shared_link_metadata.url.replace('?dl=0', '?dl=1')
        return file_link
    except dropbox.exceptions.AuthError as e:
        if refresh_access_token():
            return upload_to_dropbox(uploadedfile, filename)
        else:
            st.error("Failed to refresh access token. Please check your credentials.")
            return None

# Function to read PDF and extract Aadhaar numbers
def extract_aadhaar_from_pdf(file):
    aadhaar_numbers = []
    
    # Read the PDF file
    pdf_reader = PyPDF2.PdfReader(file)
    for page in pdf_reader.pages:
        text = page.extract_text()
        # Regex to find Aadhaar numbers (12 digits)
        found_numbers = re.findall(r'\b\d{4}\s*\d{4}\s*\d{4}\b', text)
        aadhaar_numbers.extend(found_numbers)
    
    return aadhaar_numbers

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

# Upload section
uploaded_files = st.file_uploader('Upload multiple documents (Aadhaar, PAN, etc.)', type=['pdf'], accept_multiple_files=True)

if uploaded_files is not None:
    files_metadata = []
    
    for uploaded_file in uploaded_files:
        # Upload file to Dropbox
        file_link = upload_to_dropbox(uploaded_file, uploaded_file.name)
        if file_link:
            # Check for Aadhaar numbers in the PDF
            aadhaar_numbers = extract_aadhaar_from_pdf(uploaded_file)
            document_type = "Aadhaar" if aadhaar_numbers else "Other"

            # Prepare metadata
            files_metadata.append({
                "document_url": file_link,
                "document_type": document_type,
                "aadhaar_numbers": aadhaar_numbers  # Store found Aadhaar numbers
            })
    
    if files_metadata:
        qr_image = generate_qr_code_with_metadata(files_metadata)
        qr_image_bytes = pil_image_to_bytes(qr_image)
        
        st.image(qr_image_bytes, caption='QR code with metadata for uploaded files')
        st.download_button(label="Download QR code", data=qr_image_bytes, file_name="qr_code.png", mime="image/png")
