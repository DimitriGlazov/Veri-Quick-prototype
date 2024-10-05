"""
Creating a web Server to make sure the EDV's function 
Process:
1. File upload condition  
2. Data storage and execution with the links 
3. Retrieve the file link in the QR format to make the application redirect 
to the created link 
"""

# Importing modules 
import streamlit as st
import dropbox
import qrcode
from PIL import Image
import io

# Homepage 
st.set_page_config(page_title="EDV file uploader")
st.header("EDV file uploader")
st.subheader('Upload files to store and retrieve Dropbox links and QR codes')

# Dropbox access token (Getting it from environment variables)
ACCESS_TOKEN = st.secrets["dropbox"]['access_token']

# Initialize Dropbox client
if ACCESS_TOKEN:
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
else:
    st.error("Dropbox access token is missing. Please set the environment variable 'DROPBOX_OAUTH2_KEY'.")

# Setting up file upload condition 
uploadedfiles = st.file_uploader('Upload all the documents here', type=['PDF', 'JPEG', 'JPG', 'PNG'])

# Function to upload file to Dropbox and get the link
def upload_to_dropbox(uploadedfile):
    try:
        file_path = f"/{uploadedfile.name}"
        dbx.files_upload(uploadedfile.getbuffer().tobytes(), file_path)
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        file_link = shared_link_metadata.url
        st.success(f"Successfully uploaded {uploadedfile.name} to Dropbox")
        return file_link
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {e}")
        return None

# Function to generate QR code from a link
def generate_qr_code(link):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    return img

# Function to convert PIL Image to bytes
def pil_image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    byte_im = buf.getvalue()
    return byte_im

# Upload the file to Dropbox and generate QR code
if uploadedfiles is not None:
    file_link = upload_to_dropbox(uploadedfiles)
    if file_link:
        st.markdown(f"[**Click here to download the file**]({file_link})", unsafe_allow_html=True)
        qr_image = generate_qr_code(file_link)
        qr_image_bytes = pil_image_to_bytes(qr_image)
        st.image(qr_image_bytes, caption='QR code for the file link')
