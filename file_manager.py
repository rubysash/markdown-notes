# file_manager.py
 
import hashlib
import os
import shutil
from typing import Optional, Tuple, Callable

def create_new_file(path, filename):
    new_path = os.path.join(path, filename)
    with open(new_path, "w", encoding="utf-8") as f:
        f.write("")
    return new_path

def create_new_folder(path, foldername):
    new_path = os.path.join(path, foldername)
    os.makedirs(new_path, exist_ok=True)
    return new_path

def delete_item(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def rename_item(old_path, new_path):
    os.rename(old_path, new_path)

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def calculate_md5(filepath: str, chunk_size: int = 65536, progress_callback: Optional[Callable] = None) -> str:
    """Calculate MD5 hash of a file using chunked reading to minimize memory usage."""
    hash_md5 = hashlib.md5()
    file_size = os.path.getsize(filepath)
    bytes_read = 0
    
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_md5.update(chunk)
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read, file_size)
        return hash_md5.hexdigest()
    except (IOError, OSError) as e:
        raise Exception(f"Failed to calculate MD5 for {filepath}: {str(e)}")

def verify_file_integrity(source_path: str, dest_path: str, progress_callback: Optional[Callable] = None) -> bool:
    """Verify that source and destination files are identical using MD5 comparison."""
    try:
        # Quick checks first
        if not os.path.exists(source_path) or not os.path.exists(dest_path):
            return False
        
        source_size = os.path.getsize(source_path)
        dest_size = os.path.getsize(dest_path)
        
        # Size mismatch = corruption
        if source_size != dest_size:
            return False
        
        # For very small files, size check might be sufficient
        if source_size == 0:
            return True
        
        # Calculate MD5 hashes
        source_md5 = calculate_md5(source_path, progress_callback=progress_callback)
        dest_md5 = calculate_md5(dest_path, progress_callback=progress_callback)
        
        return source_md5 == dest_md5
    except Exception:
        return False

def get_directory_stats(path: str) -> Tuple[int, int]:
    """Get total file count and size for a directory recursively."""
    total_files = 0
    total_size = 0
    
    try:
        if os.path.isfile(path):
            return 1, os.path.getsize(path)
        
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_files += 1
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    pass  # Skip files we can't access
    except (OSError, IOError):
        pass
    
    return total_files, total_size

def check_cross_drive_operation(source: str, dest: str) -> bool:
    """Check if this is a cross-drive operation."""
    try:
        source_drive = os.path.splitdrive(os.path.abspath(source))[0]
        dest_drive = os.path.splitdrive(os.path.abspath(dest))[0]
        return source_drive.upper() != dest_drive.upper()
    except Exception:
        return True  # Assume cross-drive if we can't determine

def check_permissions(source: str, dest_dir: str) -> Tuple[bool, str]:
    """Check if we have necessary permissions for the move operation."""
    try:
        # Check source read permission
        if not os.access(source, os.R_OK):
            return False, f"No read permission for source: {source}"
        
        # For directories, check all contents
        if os.path.isdir(source):
            for root, dirs, files in os.walk(source):
                for item in dirs + files:
                    item_path = os.path.join(root, item)
                    if not os.access(item_path, os.R_OK):
                        return False, f"No read permission for: {item_path}"
        
        # Check destination write permission
        if not os.access(dest_dir, os.W_OK):
            return False, f"No write permission for destination: {dest_dir}"
        
        # Check available space
        if hasattr(shutil, 'disk_usage'):
            source_size = get_directory_stats(source)[1]
            free_space = shutil.disk_usage(dest_dir).free
            if source_size > free_space:
                return False, f"Insufficient disk space. Need {source_size:,} bytes, have {free_space:,} bytes"
        
        return True, ""
    except Exception as e:
        return False, f"Permission check failed: {str(e)}"