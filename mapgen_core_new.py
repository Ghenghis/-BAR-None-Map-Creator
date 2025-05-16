import numpy as np
from PIL import Image
import random
import os
import shutil
from scipy.ndimage import gaussian_filter

class BARMapGenerator:
    def __init__(self, output_dir="generated_maps"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_heightmap(self, size=1024, hill_count=20, smoothing=5):
        """Generate a basic heightmap with hills and valleys"""
        heightmap = np.zeros((size, size), dtype=np.float32)

        # Add random hills
        for _ in range(hill_count):
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            radius = random.randint(50, 200)
            height = random.uniform(0.2, 1.0)

            for i in range(max(0, x-radius), min(size, x+radius)):
                for j in range(max(0, y-radius), min(size, y+radius)):
                    dist = np.sqrt((i-x)**2 + (j-y)**2)
                    if dist < radius:
                        heightmap[i, j] += height * (1 - dist/radius)

        # Apply smoothing
        if smoothing > 0:
            heightmap = gaussian_filter(heightmap, sigma=smoothing)

        # Normalize to 0-1 range
        if np.max(heightmap) > np.min(heightmap):  # Avoid division by zero
            heightmap = (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))

        return heightmap

    def save_heightmap(self, heightmap, name="heightmap", format="png"):
        """Save heightmap to file and return the directory path"""
        # Create directory for the map
        map_dir = os.path.join(self.output_dir, name)
        os.makedirs(map_dir, exist_ok=True)

        # Save as image
        if format == "png":
            # Convert to 16-bit grayscale image
            img_array = (heightmap * 65535).astype(np.uint16)
            img = Image.fromarray(img_array, mode='I')
            img.save(os.path.join(map_dir, "heightmap.png"))
        else:
            # Save as raw data
            with open(os.path.join(map_dir, "heightmap.raw"), 'wb') as f:
                ((heightmap * 65535).astype(np.uint16)).tofile(f)

        return map_dir

    def generate_preview(self, heightmap, size=512):
        """Generate a preview image from heightmap"""
        # Create a copy of the heightmap for visualization
        preview = heightmap.copy()
        
        # Convert to RGB
        rgb = np.zeros((preview.shape[0], preview.shape[1], 3), dtype=np.uint8)
        
        # Create a terrain-like coloring
        for i in range(preview.shape[0]):
            for j in range(preview.shape[1]):
                h = preview[i, j]
                if h < 0.2:  # Deep water
                    rgb[i, j] = [0, 0, 150]
                elif h < 0.3:  # Shallow water
                    rgb[i, j] = [0, 50, 200]
                elif h < 0.4:  # Beach
                    rgb[i, j] = [240, 240, 160]
                elif h < 0.7:  # Grass/forest
                    g = int(100 + h * 100)
                    rgb[i, j] = [0, g, 0]
                else:  # Mountain
                    v = int(200 + h * 55)
                    rgb[i, j] = [v, v, v]
        
        # Create image and resize
        img = Image.fromarray(rgb, mode='RGB')
        if size != preview.shape[0]:
            img = img.resize((size, size), Image.LANCZOS)
        
        # Save preview
        preview_path = os.path.join(self.output_dir, "preview.png")
        img.save(preview_path)
        
        return preview_path

    def generate_metal_spots(self, heightmap, num_spots=20, min_distance=50):
        """Generate metal spot positions based on heightmap"""
        spots = []
        size = heightmap.shape[0]
        attempts = 0
        max_attempts = num_spots * 100  # Limit attempts to avoid infinite loops
        
        while len(spots) < num_spots and attempts < max_attempts:
            attempts += 1
            
            # Generate random position
            x = random.randint(50, size - 50)
            y = random.randint(50, size - 50)
            
            # Check height (not too high, not too low)
            h = heightmap[x, y]
            if h < 0.3 or h > 0.8:  # Not in water, not on mountain peaks
                continue
            
            # Check distance from other spots
            too_close = False
            for sx, sy in spots:
                dist = np.sqrt((x - sx)**2 + (y - sy)**2)
                if dist < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                spots.append((x, y))
        
        return spots

    def create_map_config(self, map_dir, name, description, metal_spots):
        """Create mapinfo.lua and other config files"""
        # Create mapinfo.lua
        mapinfo_content = f"""
local mapinfo = {{
    name        = "{name}",
    shortname   = "{name}",
    description = "{description}",
    author      = "AI Map Creator",
    version     = "1.0",
    mapfile     = "{name}.smf",
    modtype     = 3, -- PBP
    
    -- Size and dimensions
    mapsizeX    = 8,
    mapsizeZ    = 8,
    mapx        = 8192,
    mapy        = 8192,
    
    -- Resources
    maxmetal    = 2.0,
    extractorradius = 125.0,
    
    -- Features
    smf         = true,
    gravity     = 130,
    tidalstrength = 0,
    maxslope    = 80,
    atmosphere  = {{ minWind = 5, maxWind = 25 }},
    water       = {{ damage = 0 }},
    
    -- Terrain
    terrainType = "default",
    
    -- Custom resources
    custom_resources = {{
"""
        
        # Add metal spots
        for i, (x, y) in enumerate(metal_spots):
            # Convert from heightmap coordinates to game coordinates
            game_x = (x / heightmap.shape[0]) * 8192
            game_z = (y / heightmap.shape[0]) * 8192
            mapinfo_content += f"        {{ name = \"metal\", x = {game_x}, z = {game_z} }},\n"
        
        mapinfo_content += """
    }
}
return mapinfo
"""
        
        # Write mapinfo.lua
        with open(os.path.join(map_dir, "mapinfo.lua"), 'w') as f:
            f.write(mapinfo_content)
        
        # Create minimap
        self.create_minimap(map_dir, heightmap)

    def create_minimap(self, map_dir, heightmap, size=1024):
        """Create minimap.png for the map"""
        # Create a colored version of the heightmap
        rgb = np.zeros((heightmap.shape[0], heightmap.shape[1], 3), dtype=np.uint8)
        
        # Create a terrain-like coloring (similar to preview but higher quality)
        for i in range(heightmap.shape[0]):
            for j in range(heightmap.shape[1]):
                h = heightmap[i, j]
                if h < 0.2:  # Deep water
                    rgb[i, j] = [0, 0, 150]
                elif h < 0.3:  # Shallow water
                    rgb[i, j] = [0, 50, 200]
                elif h < 0.4:  # Beach
                    rgb[i, j] = [240, 240, 160]
                elif h < 0.7:  # Grass/forest
                    g = int(100 + h * 100)
                    rgb[i, j] = [0, g, 0]
                else:  # Mountain
                    v = int(200 + h * 55)
                    rgb[i, j] = [v, v, v]
        
        # Create image
        minimap = Image.fromarray(rgb, mode='RGB')
        
        # Save minimap
        minimap.save(os.path.join(map_dir, "minimap.png"))

    def generate_textures(self, heightmap, map_dir):
        """Generate textures based on heightmap"""
        # Create a simple texture based on height
        texture = np.zeros((heightmap.shape[0], heightmap.shape[1], 3), dtype=np.uint8)
        
        # Create different textures based on height
        for i in range(heightmap.shape[0]):
            for j in range(heightmap.shape[1]):
                h = heightmap[i, j]
                if h < 0.2:  # Water
                    texture[i, j] = [0, 0, 100]
                elif h < 0.3:  # Shore
                    texture[i, j] = [200, 200, 100]
                elif h < 0.7:  # Land
                    g = int(100 + h * 100)
                    texture[i, j] = [50, g, 50]
                else:  # Mountain
                    v = int(150 + h * 100)
                    texture[i, j] = [v, v, v]
        
        # Save texture
        img = Image.fromarray(texture, mode='RGB')
        img.save(os.path.join(map_dir, "texture.png"))

    def create_map_archive(self, map_dir, name):
        """Create a directory with all map files for easy copying"""
        # Create archive directory
        archive_dir = os.path.join(self.output_dir, f"{name}_archive")
        os.makedirs(archive_dir, exist_ok=True)
        
        # Copy all files from map_dir to archive_dir
        for file in os.listdir(map_dir):
            shutil.copy2(os.path.join(map_dir, file), os.path.join(archive_dir, file))
            
        return archive_dir

    def generate_complete_map(self, name="AI_Generated_Map", description="AI generated terrain", 
                             size=1024, hill_count=20, metal_spots=20):
        """Generate a complete map with all required files"""
        # Generate heightmap
        heightmap = self.generate_heightmap(size=size, hill_count=hill_count)
        
        # Save heightmap
        map_dir = self.save_heightmap(heightmap, name=name)
        
        # Generate metal spots
        spots = self.generate_metal_spots(heightmap, num_spots=metal_spots)
        
        # Create map config
        self.create_map_config(map_dir, name, description, spots)
        
        # Generate textures
        self.generate_textures(heightmap, map_dir)
        
        # Create archive
        archive_dir = self.create_map_archive(map_dir, name)
        
        return archive_dir
