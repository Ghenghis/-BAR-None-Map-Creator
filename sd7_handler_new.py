import os
import zipfile
import hashlib
import gzip
import shutil
import tempfile
import logging
import json
import re
from pathlib import Path

class SD7Handler:
    """
    Handles packing and unpacking of SD7 map files for Beyond All Reason.
    Includes MD5 checksum generation for compatibility and tools for editing extracted maps.
    """

    def __init__(self, maps_directory=None, generated_maps_directory=None):
        """
        Initialize the SD7 handler.

        Args:
            maps_directory: Path to BAR maps directory (optional)
            generated_maps_directory: Path to generated maps directory (optional)
        """
        self.logger = logging.getLogger('SD7Handler')
        
        # Set up logging if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Set default directories if not provided
        if not maps_directory:
            self.maps_directory = os.path.expanduser("C:\\Users\\Admin\\AppData\\Local\\Programs\\Beyond-All-Reason\\data\\maps")
        else:
            self.maps_directory = maps_directory
            
        if not generated_maps_directory:
            self.generated_maps_directory = os.path.expanduser("C:\\Users\\Admin\\BAR-MapCreator\\generated_maps\\AI_Generated_Map")
        else:
            self.generated_maps_directory = generated_maps_directory
            
        # Create directories if they don't exist
        os.makedirs(self.maps_directory, exist_ok=True)
        os.makedirs(self.generated_maps_directory, exist_ok=True)
        
        self.logger.info(f"Maps directory: {self.maps_directory}")
        self.logger.info(f"Generated maps directory: {self.generated_maps_directory}")

    def list_installed_maps(self):
        """
        List all installed maps in the BAR maps directory.
        
        Returns:
            List of map names (without extension)
        """
        if not self.maps_directory or not os.path.exists(self.maps_directory):
            self.logger.error("Maps directory not set or doesn't exist")
            return []
            
        maps = []
        for file in os.listdir(self.maps_directory):
            if file.endswith('.sd7'):
                maps.append(os.path.splitext(file)[0])
        return maps
        
    def get_map_path(self, map_name):
        """
        Get the full path to a map file.
        
        Args:
            map_name: Name of the map (with or without .sd7 extension)
            
        Returns:
            Full path to the map file
        """
        if not map_name.endswith('.sd7'):
            map_name = f"{map_name}.sd7"
            
        return os.path.join(self.maps_directory, map_name)
    
    def extract_map(self, map_name, output_dir=None):
        """
        Extract a map to a directory for editing.
        
        Args:
            map_name: Name of the map (with or without .sd7 extension)
            output_dir: Directory to extract to (default: temp directory)
            
        Returns:
            Path to the extracted directory
        """
        # Handle both map names and full paths
        if os.path.exists(map_name) and map_name.endswith('.sd7'):
            map_path = map_name
        else:
            map_path = self.get_map_path(map_name)
        
        if not os.path.exists(map_path):
            self.logger.error(f"SD7 file not found: {map_path}")
            return None
            
        # Create a temporary directory if output_dir is not specified
        if not output_dir:
            map_basename = os.path.basename(map_path)
            map_name_no_ext = os.path.splitext(map_basename)[0]
            output_dir = os.path.join(tempfile.gettempdir(), f"bar_map_edit_{map_name_no_ext}")
            
        # Clear the output directory if it exists
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Extract the SD7 file
            with zipfile.ZipFile(map_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
                
            self.logger.info(f"Extracted {map_path} to {output_dir}")
            return output_dir
        except Exception as e:
            self.logger.error(f"Error extracting map: {str(e)}")
            return None

    def get_map_info(self, map_name):
        """
        Get information about a map.
        
        Args:
            map_name: Name of the map (with or without .sd7 extension)
            
        Returns:
            Dictionary with map information
        """
        # Handle both map names and full paths
        if os.path.exists(map_name) and map_name.endswith('.sd7'):
            map_path = map_name
        else:
            map_path = self.get_map_path(map_name)
        
        if not os.path.exists(map_path):
            self.logger.error(f"SD7 file not found: {map_path}")
            return {"name": os.path.basename(map_path), "error": "File not found"}
        
        # Extract the map to a temporary directory
        temp_dir = self.extract_map(map_path)
        if not temp_dir:
            return {"name": os.path.basename(map_path), "error": "Failed to extract map"}
        
        try:
            # Get map structure
            structure = self.get_map_structure(temp_dir)
            
            # Parse mapinfo.lua if it exists
            mapinfo = self._parse_mapinfo(temp_dir)
            
            # Combine information
            info = {
                "name": os.path.splitext(os.path.basename(map_path))[0],
                "path": map_path,
                "size": os.path.getsize(map_path),
                "structure": structure,
                "mapinfo": mapinfo
            }
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            return info
        except Exception as e:
            self.logger.error(f"Error getting map info: {str(e)}")
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {"name": os.path.basename(map_path), "error": str(e)}
    
    def _parse_mapinfo(self, map_dir):
        """
        Parse mapinfo.lua file to extract map metadata.
        
        Args:
            map_dir: Directory containing the extracted map
            
        Returns:
            Dictionary with map metadata
        """
        mapinfo_path = os.path.join(map_dir, "mapinfo.lua")
        if not os.path.exists(mapinfo_path):
            return {"error": "mapinfo.lua not found"}
        
        try:
            with open(mapinfo_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract basic information using regex
            info = {}
            
            # Extract map name
            name_match = re.search(r'name\s*=\s*["\']([^"\']*)["\']', content)
            if name_match:
                info["name"] = name_match.group(1)
                
            # Extract map description
            desc_match = re.search(r'description\s*=\s*["\']([^"\']*)["\']', content)
            if desc_match:
                info["description"] = desc_match.group(1)
                
            # Extract author
            author_match = re.search(r'author\s*=\s*["\']([^"\']*)["\']', content)
            if author_match:
                info["author"] = author_match.group(1)
                
            # Extract size
            size_match = re.search(r'mapx\s*=\s*(\d+)', content)
            sizey_match = re.search(r'mapy\s*=\s*(\d+)', content)
            if size_match and sizey_match:
                info["size"] = f"{size_match.group(1)}x{sizey_match.group(1)}"
                
            return info
        except Exception as e:
            self.logger.error(f"Error parsing mapinfo.lua: {str(e)}")
            return {"error": f"Failed to parse mapinfo.lua: {str(e)}"}

    def get_map_structure(self, extracted_dir):
        """
        Analyze the structure of an extracted map.
        
        Args:
            extracted_dir: Path to the extracted map directory
            
        Returns:
            Dictionary with map structure information
        """
        if not os.path.exists(extracted_dir):
            self.logger.error(f"Extracted directory not found: {extracted_dir}")
            return {"error": "Directory not found"}
            
        try:
            structure = {
                "files": [],
                "directories": [],
                "has_heightmap": False,
                "has_metalmap": False,
                "has_minimap": False,
                "has_mapinfo": False,
                "has_textures": False,
                "total_size": 0
            }
            
            # Walk through the directory
            for root, dirs, files in os.walk(extracted_dir):
                # Add directories to structure
                rel_path = os.path.relpath(root, extracted_dir)
                if rel_path != '.':
                    structure["directories"].append(rel_path)
                
                # Process files
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.join(rel_path, file).replace('.\\', '')
                    if rel_path == '.':
                        rel_file_path = file
                    
                    file_size = os.path.getsize(file_path)
                    
                    # Add file info
                    structure["files"].append({
                        "path": rel_file_path,
                        "size": file_size
                    })
                    
                    # Update total size
                    structure["total_size"] += file_size
                    
                    # Check for specific files
                    lower_file = file.lower()
                    if 'height' in lower_file and lower_file.endswith(('.raw', '.png')):
                        structure["has_heightmap"] = True
                    elif 'metal' in lower_file and lower_file.endswith(('.raw', '.png')):
                        structure["has_metalmap"] = True
                    elif 'minimap' in lower_file and lower_file.endswith(('.png', '.jpg', '.dds')):
                        structure["has_minimap"] = True
                    elif lower_file == 'mapinfo.lua':
                        structure["has_mapinfo"] = True
                    elif lower_file.endswith(('.png', '.jpg', '.dds')) and ('texture' in lower_file or 'textures' in root.lower()):
                        structure["has_textures"] = True
            
            return structure
        except Exception as e:
            self.logger.error(f"Error analyzing map structure: {str(e)}")
            return {"error": f"Failed to analyze structure: {str(e)}"}

    def create_sd7(self, source_dir, output_filename=None):
        """
        Create a SD7 file from a directory.
        
        Args:
            source_dir: Directory containing map files
            output_filename: Name of the output SD7 file (default: based on directory name)
            
        Returns:
            Path to the created SD7 file
        """
        if not os.path.exists(source_dir):
            self.logger.error(f"Source directory not found: {source_dir}")
            return None
            
        # Determine output filename if not specified
        if not output_filename:
            dir_name = os.path.basename(source_dir)
            output_filename = os.path.join(self.maps_directory, f"{dir_name}.sd7")
        elif not output_filename.endswith('.sd7'):
            output_filename = f"{output_filename}.sd7"
            
        # If output_filename doesn't have a path, add maps_directory
        if os.path.dirname(output_filename) == '':
            output_filename = os.path.join(self.maps_directory, output_filename)
            
        try:
            # Create the SD7 file (zip format)
            with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through the directory and add all files
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path for the archive
                        rel_path = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, rel_path)
            
            self.logger.info(f"Created SD7 file: {output_filename}")
            
            # Generate MD5 checksum file
            self.generate_md5(output_filename)
            
            return output_filename
        except Exception as e:
            self.logger.error(f"Error creating SD7 file: {str(e)}")
            return None

    def generate_md5(self, sd7_filename):
        """
        Generate MD5 checksum file for a SD7 file.
        
        Args:
            sd7_filename: Path to the SD7 file
            
        Returns:
            Path to the generated MD5 file
        """
        if not os.path.exists(sd7_filename):
            self.logger.error(f"SD7 file not found: {sd7_filename}")
            return None
            
        try:
            # Calculate MD5 checksum
            md5_hash = hashlib.md5()
            with open(sd7_filename, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            
            # Create MD5 filename
            md5_filename = f"{sd7_filename}.md5"
            
            # Write MD5 to file
            with open(md5_filename, 'w') as f:
                f.write(md5_hash.hexdigest())
            
            # Compress MD5 file with gzip
            with open(md5_filename, 'rb') as f_in:
                with gzip.open(f"{md5_filename}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove the uncompressed MD5 file
            os.remove(md5_filename)
            
            self.logger.info(f"Generated MD5 checksum: {md5_filename}.gz")
            return f"{md5_filename}.gz"
        except Exception as e:
            self.logger.error(f"Error generating MD5 checksum: {str(e)}")
            return None

    def verify_md5(self, sd7_filename):
        """
        Verify the MD5 checksum of a SD7 file.
        
        Args:
            sd7_filename: Path to the SD7 file
            
        Returns:
            True if verified, False if not
        """
        if not os.path.exists(sd7_filename):
            self.logger.error(f"SD7 file not found: {sd7_filename}")
            return False
            
        md5_filename = f"{sd7_filename}.md5.gz"
        if not os.path.exists(md5_filename):
            self.logger.error(f"MD5 file not found: {md5_filename}")
            return False
            
        try:
            # Calculate current MD5
            md5_hash = hashlib.md5()
            with open(sd7_filename, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            current_md5 = md5_hash.hexdigest()
            
            # Read stored MD5
            with gzip.open(md5_filename, 'rb') as f:
                stored_md5 = f.read().decode('utf-8').strip()
            
            # Compare
            if current_md5 == stored_md5:
                self.logger.info(f"MD5 checksum verified for: {sd7_filename}")
                return True
            else:
                self.logger.warning(f"MD5 checksum mismatch for: {sd7_filename}")
                self.logger.warning(f"Stored: {stored_md5}")
                self.logger.warning(f"Calculated: {current_md5}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying MD5 checksum: {str(e)}")
            return False

    def install_map(self, sd7_filename, verify=True):
        """
        Install a map to the BAR maps directory.
        
        Args:
            sd7_filename: Path to the SD7 file
            verify: Whether to verify the MD5 checksum after installation
            
        Returns:
            True if installed successfully, False if not
        """
        if not os.path.exists(sd7_filename):
            self.logger.error(f"SD7 file not found: {sd7_filename}")
            return False
            
        try:
            # Copy the SD7 file to the maps directory
            dest_path = os.path.join(self.maps_directory, os.path.basename(sd7_filename))
            shutil.copy2(sd7_filename, dest_path)
            
            # Copy the MD5 file if it exists
            md5_path = f"{sd7_filename}.md5.gz"
            if os.path.exists(md5_path):
                shutil.copy2(md5_path, f"{dest_path}.md5.gz")
            else:
                # Generate MD5 if it doesn't exist
                self.generate_md5(dest_path)
            
            self.logger.info(f"Installed map: {dest_path}")
            
            # Verify the installation if requested
            if verify:
                return self.verify_md5(dest_path)
            return True
        except Exception as e:
            self.logger.error(f"Error installing map: {str(e)}")
            return False

    def edit_map(self, map_name):
        """
        Extract a map for editing and return the path to the extracted directory.
        
        Args:
            map_name: Name of the map (with or without .sd7 extension)
            
        Returns:
            Path to the extracted directory
        """
        # Extract the map to a temporary directory
        extract_dir = self.extract_map(map_name)
        if not extract_dir:
            return None
            
        self.logger.info(f"Map extracted for editing: {extract_dir}")
        return extract_dir

    def save_edited_map(self, edited_dir, output_name=None, install=True):
        """
        Save an edited map as a new SD7 file.
        
        Args:
            edited_dir: Directory containing the edited map
            output_name: Name for the new map (default: original name with _edited suffix)
            install: Whether to install the map to the BAR maps directory
            
        Returns:
            Path to the created SD7 file
        """
        if not os.path.exists(edited_dir):
            self.logger.error(f"Edited directory not found: {edited_dir}")
            return None
            
        # Determine output name if not specified
        if not output_name:
            dir_name = os.path.basename(edited_dir)
            if dir_name.startswith("bar_map_edit_"):
                dir_name = dir_name[len("bar_map_edit_"):]
            output_name = f"{dir_name}_edited"
            
        # Create the SD7 file
        sd7_path = self.create_sd7(edited_dir, output_name)
        if not sd7_path:
            return None
            
        # Install the map if requested
        if install:
            self.install_map(sd7_path)
            
        return sd7_path

    def copy_map_from_generated(self, map_name=None, install=True):
        """
        Copy a map from the generated maps directory to the BAR maps directory.
        
        Args:
            map_name: Name of the map (default: use directory name)
            install: Whether to install the map to the BAR maps directory
            
        Returns:
            Path to the created SD7 file
        """
        if not os.path.exists(self.generated_maps_directory):
            self.logger.error(f"Generated maps directory not found: {self.generated_maps_directory}")
            return None
            
        # Determine map name if not specified
        if not map_name:
            map_name = os.path.basename(self.generated_maps_directory)
            
        # Create the SD7 file
        sd7_path = self.create_sd7(self.generated_maps_directory, map_name)
        if not sd7_path:
            return None
            
        # Install the map if requested
        if install:
            self.install_map(sd7_path)
            
        return sd7_path

    def update_mapinfo(self, map_dir, name=None, description=None, author=None, size_x=None, size_y=None):
        """
        Update the mapinfo.lua file in an extracted map directory.
        
        Args:
            map_dir: Directory containing the extracted map
            name: New map name (optional)
            description: New map description (optional)
            author: New map author (optional)
            size_x: New map width (optional)
            size_y: New map height (optional)
            
        Returns:
            True if updated successfully, False if not
        """
        mapinfo_path = os.path.join(map_dir, "mapinfo.lua")
        if not os.path.exists(mapinfo_path):
            self.logger.error(f"mapinfo.lua not found in: {map_dir}")
            return False
            
        try:
            # Read the current mapinfo.lua
            with open(mapinfo_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Update the fields
            if name:
                content = re.sub(r'(name\s*=\s*)["\']([^"\']*)["\']', f'\\1"{name}"', content)
            if description:
                content = re.sub(r'(description\s*=\s*)["\']([^"\']*)["\']', f'\\1"{description}"', content)
            if author:
                content = re.sub(r'(author\s*=\s*)["\']([^"\']*)["\']', f'\\1"{author}"', content)
            if size_x:
                content = re.sub(r'(mapx\s*=\s*)(\d+)', f'\\1{size_x}', content)
            if size_y:
                content = re.sub(r'(mapy\s*=\s*)(\d+)', f'\\1{size_y}', content)
                
            # Write the updated mapinfo.lua
            with open(mapinfo_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"Updated mapinfo.lua in: {map_dir}")

# Example usage
if __name__ == "__main__":
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create SD7 handler
handler = SD7Handler()

# List installed maps
maps = handler.list_installed_maps()
print(f"Found {len(maps)} installed maps")

if maps:
# Get info about first map
map_info = handler.get_map_info(maps[0])
print(f"Map info: {json.dumps(map_info, indent=2)}")

# Extract the map
extract_dir = handler.extract_map(maps[0])
if extract_dir:
print(f"Extracted to: {extract_dir}")

# Analyze structure of extracted map
structure = handler.get_map_structure(extract_dir)
print(f"Map structure: {json.dumps(structure, indent=2)}")

# Create a new SD7 (for testing)
new_sd7 = handler.create_sd7(extract_dir, "test_map.sd7")
if new_sd7:
print(f"Created new SD7: {new_sd7}")

# Verify MD5
verified = handler.verify_md5(new_sd7)
print(f"MD5 verified: {verified}")
else:
print("No maps found. Try copying a map from the generated maps directory.")

# Copy a map from the generated maps directory
sd7_path = handler.copy_map_from_generated("AI_Generated_Map")
if sd7_path:
print(f"Created SD7 from generated map: {sd7_path}")
    handler = SD7Handler()
    
    # List installed maps
    maps = handler.list_installed_maps()
    print(f"Found {len(maps)} installed maps")
    
    if maps:
        # Get info about first map
        map_info = handler.get_map_info(maps[0])
        print(f"Map info: {json.dumps(map_info, indent=2)}")
        
        # Extract the map
        extract_dir = handler.extract_map(maps[0])
        if extract_dir:
            print(f"Extracted to: {extract_dir}")
            
            # Analyze structure of extracted map
            structure = handler.get_map_structure(extract_dir)
            print(f"Map structure: {json.dumps(structure, indent=2)}")
            
            # Create a new SD7 (for testing)
            new_sd7 = handler.create_sd7(extract_dir, "test_map.sd7")
            if new_sd7:
                print(f"Created new SD7: {new_sd7}")
                
                # Verify MD5
                verified = handler.verify_md5(new_sd7)
                print(f"MD5 verified: {verified}")
    else:
        print("No maps found. Try copying a map from the generated maps directory.")
        
        # Copy a map from the generated maps directory
        sd7_path = handler.copy_map_from_generated("AI_Generated_Map")
        if sd7_path:
            print(f"Created SD7 from generated map: {sd7_path}")
