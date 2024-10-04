import os
import shutil
import glob
from PIL import Image
import tempfile
import zipfile

# Constants
EPUB_EXTENSION = '.epub'
COMPRESSED_FOLDER_NAME = 'compressed_files'
MAX_IMAGE_HEIGHT = 320  # Maximum height in pixels

def find_epub_files(folder_path):
    """
    Retrieves all EPUB files in the specified folder.
    """
    pattern = os.path.join(folder_path, f'*{EPUB_EXTENSION}')
    epub_files = glob.glob(pattern)
    return epub_files

def unpack_epub(epub_path, extract_to):
    """
    Unpacks the EPUB file (which is a ZIP archive) to the specified directory.
    """
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Unpacked: {epub_path}")
    except zipfile.BadZipFile:
        print(f"Error: '{epub_path}' is not a valid EPUB file.")
        raise

def find_image_folders(extract_path):
    """
    Finds common image directories within the EPUB structure.
    Typically, images are stored in 'images', 'img', or 'image' folders.
    """
    image_folders = []
    for root, dirs, files in os.walk(extract_path):
        for dir_name in dirs:
            if dir_name.lower() in ['images', 'img', 'image']:
                image_folders.append(os.path.join(root, dir_name))
    return image_folders

def resize_image(image, max_height):
    """
    Resizes the image to ensure its height does not exceed max_height pixels,
    maintaining the aspect ratio.
    """
    width, height = image.size
    if height > max_height:
        # Calculate the new width to maintain aspect ratio
        new_width = int((max_height / height) * width)
        resized_image = image.resize((new_width, max_height), Image.LANCZOS)
        return resized_image
    return image  # Return original image if resizing is not needed

def compress_image(image_path, quality=10, max_height=320):
    """
    Compresses and resizes an image to the specified quality and maximum height.
    """
    try:
        with Image.open(image_path) as img:
            original_format = img.format
            # Resize the image if necessary
            img = resize_image(img, max_height)

            if original_format in ['JPEG', 'JPG']:
                img.save(image_path, 'JPEG', optimize=True, quality=quality)
            elif original_format == 'PNG':
                # For PNGs, reduce colors to decrease size
                img = img.convert('P', palette=Image.ADAPTIVE, colors=64)
                img.save(image_path, 'PNG', optimize=True)
            else:
                # Skip other formats to avoid data loss
                print(f"Skipped unsupported image format: {image_path}")
    except Exception as e:
        print(f"Failed to process image '{image_path}': {e}")

def compress_images_in_folders(image_folders, quality=10, max_height=320):
    """
    Compresses and resizes all images in the provided list of image folders.
    """
    for folder in image_folders:
        print(f"Compressing and resizing images in: {folder}")
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(root, file)
                    compress_image(image_path, quality, max_height)

def repack_epub(extract_path, output_epub_path):
    """
    Repackages the extracted EPUB directory into an EPUB file.
    """
    with zipfile.ZipFile(output_epub_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Preserve the EPUB's internal directory structure
                arcname = os.path.relpath(file_path, extract_path)
                zipf.write(file_path, arcname)
    print(f"Repacked EPUB: {output_epub_path}")

def process_epub(epub_path, compressed_dir, compression_quality=10, max_height=320):
    """
    Processes a single EPUB file: unpacks, compresses and resizes images, and repacks.
    The compressed EPUB is saved in the compressed_dir without renaming.
    """
    try:
        # Create a temporary directory for unpacking
        with tempfile.TemporaryDirectory() as temp_dir:
            unpack_epub(epub_path, temp_dir)
            image_folders = find_image_folders(temp_dir)
            
            if not image_folders:
                print(f"No image folders found in '{epub_path}'. Skipping compression.")
                return
            
            compress_images_in_folders(image_folders, quality=compression_quality, max_height=max_height)
            
            # Define output EPUB path in the compressed_files directory
            base_name = os.path.basename(epub_path)
            output_epub = os.path.join(compressed_dir, base_name)
            
            repack_epub(temp_dir, output_epub)
            
    except Exception as e:
        print(f"Failed to process '{epub_path}': {e}")

def main():
    folder_path = r"C:\Users\ASUS\Desktop\EPUBs"  # Update this path as needed
    compression_quality = 10  # Adjust quality (1-100), lower means higher compression
    max_image_height = 320   # Maximum image height in pixels

    if not os.path.isdir(folder_path):
        print(f"The folder path '{folder_path}' does not exist.")
        return

    # Create compressed_files directory
    compressed_dir = os.path.join(folder_path, COMPRESSED_FOLDER_NAME)
    os.makedirs(compressed_dir, exist_ok=True)
    print(f"Compressed files will be saved to: {compressed_dir}")

    epub_files = find_epub_files(folder_path)

    if not epub_files:
        print(f"No EPUB files found in '{folder_path}'.")
        return

    print(f"Found {len(epub_files)} EPUB file(s) in '{folder_path}'. Starting compression...")

    for epub in epub_files:
        print(f"\nProcessing '{os.path.basename(epub)}'...")
        process_epub(epub, compressed_dir, compression_quality, max_image_height)

    print("\nCompression and resizing process completed.")

if __name__ == "__main__":
    main()
