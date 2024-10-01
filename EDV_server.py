''' Creating a web Server to make sure the EDV's function 
 Process : -
1: File upload condition  
2: Data storage and excecution with the links 
3: Retrieve the file link in the QR format to make the application redirect 
to the created link 
'''

# importing modules 
import streamlit as st
import numpy as np 
import os 
import qrcode
import pyzbar

# Homepage 
st.set_page_config(page_title="EDV file uploader")
st.header("EDV file uploader")
st.subheader('Upload files to store and retrieve QR codes')

# Setting up file upload condition 
uploadedfiles = st.file_uploader('Upload all the documents here', type=['PDF', 'JPEG', 'JPG', 'PNG'])

# Instructions 

# If the files are uploaded then 
if uploadedfiles is not None:
    st.success('File uploaded successfully')
else:
    st.warning("File wasn't uploaded, please reupload the file")

# Storing the data  
if not os.path.exists('uploaded_files'):
    os.makedirs('uploaded_files')

def save_upload(uploadedfile):
    try:
        with open(os.path.join('uploaded_files', uploadedfile.name), 'wb') as file:
            file.write(uploadedfile.getbuffer())
        st.success(f"Successfully saved the file: {uploadedfile.name} in directory")
    except Exception as e:
        st.error(f"An error occurred while saving the file: {e}")

if uploadedfiles is not None:
    save_upload(uploadedfiles)

