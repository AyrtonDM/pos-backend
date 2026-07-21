from uuid import uuid4
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
import os

# We don't need to manually configure cloudinary here if CLOUDINARY_URL is in the environment
# since the cloudinary SDK automatically picks it up, but it's good practice to ensure it's loaded.

def save_product_image(file: UploadFile) -> str:
    suffix = (file.filename or "").split('.')[-1] if '.' in (file.filename or "") else "jpg"
    filename = f"products/{uuid4().hex}"
    
    # We must reset the file pointer just in case it was read
    file.file.seek(0)
    
    response = cloudinary.uploader.upload(
        file.file,
        public_id=filename,
        folder="pos_si2"
    )
    
    return response.get("secure_url")