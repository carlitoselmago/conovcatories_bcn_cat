# resets the status of all data documents from _done to not "done"

import os
from pathlib import Path

def remove_done_from_filenames(root_dir='.'):
    """
    Simple version: recursively remove '_done' from filenames
    """
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*_done*'):
        if file_path.is_file() and '_done' in file_path.name:
            new_name = file_path.name.replace('_done', '')
            
            # Skip if new name would be empty
            if not new_name.strip():
                continue
                
            new_path = file_path.parent / new_name
            
            # Avoid overwriting existing files
            if not new_path.exists():
                try:
                    file_path.rename(new_path)
                    print(f"Renamed: {file_path.name} -> {new_name}")
                except Exception as e:
                    print(f"Error renaming {file_path}: {e}")

if __name__ == "__main__":
    # Usage: python script.py [optional_directory_path]
    import sys
    directory = "data"
    remove_done_from_filenames(directory)