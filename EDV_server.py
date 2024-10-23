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
import requests

# Homepage 
st.set_page_config(page_title=" 🗄️ EDV file uploader")
st.header("EDV file uploader")
st.subheader('Upload files to store and retrieve Dropbox links and QR codes')

# Get secrets from Streamlit secrets management
ACCESS_TOKEN = st.secrets["dropbox"]["access_token"]
REFRESH_TOKEN = st.secrets["dropbox"]["refresh_token"]
CLIENT_ID = st.secrets["dropbox"]["client_id"]
CLIENT_SECRET = st.secrets["dropbox"]["client_secret"]

# Initialize Dropbox client
if ACCESS_TOKEN:
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
else:
    st.error("Dropbox access token is missing. Please set the environment variable 'DROPBOX_OAUTH2_KEY'.")

# Setting up file upload condition 
uploaded_files = st.file_uploader('Upload all the documents here', type=['PDF', 'JPEG', 'JPG', 'PNG'], accept_multiple_files=True)

# Function to upload file to Dropbox and get the link
def upload_to_dropbox(uploaded_file):
    try:
        file_path = f"/{uploaded_file.name}"
        dbx.files_upload(uploaded_file.getbuffer().tobytes(), file_path)
        shared_link_metadata = dbx.sharing_list_shared_links(file_path)
        if shared_link_metadata.links:
            st.success(f"A shared link already exists for {uploaded_file.name}.")
            file_link = shared_link_metadata.links[0].url
        else:
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
            file_link = shared_link_metadata.url
            st.success(f"Successfully uploaded {uploaded_file.name} to Dropbox")
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

# Refresh access token function
def refresh_access_token(refresh_token):
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get("access_token"), response.json().get("refresh_token")
    else:
        st.error(f"Failed to refresh access token: {response.json()}")
        return None, None

# Check if access token is still valid (you may implement your own logic for this)
def check_access_token():
    try:
        dbx.users_get_current_account()
        return True
    except dropbox.exceptions.AuthError:
        return False

# Upload multiple files to Dropbox and generate QR codes
if uploaded_files:
    if not check_access_token():
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(REFRESH_TOKEN)
        dbx = dropbox.Dropbox(ACCESS_TOKEN)

    # Loop through each file and process it
    for uploaded_file in uploaded_files:
        file_link = upload_to_dropbox(uploaded_file)
        if file_link:
            st.markdown(f"[**View the file {uploaded_file.name}**]({file_link})", unsafe_allow_html=True)
            
            # Generate and display the QR code for the file link
            qr_image = generate_qr_code(file_link)
            qr_image_bytes = pil_image_to_bytes(qr_image)
            st.image(qr_image_bytes, caption=f'QR code for {uploaded_file.name}')
            
            # Provide download button for each QR code
            st.download_button(label=f"Download QR code for {uploaded_file.name}",
                               data=qr_image_bytes,
                               file_name=f"qr_code_{uploaded_file.name}.png",
                               mime="image/png")
