import numpy as np
from PIL import Image
import random
import os
import shutil
from scipy.ndimage import gaussian_filter

# Import SD7 handler
from sd7_handler import SD7Handler

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
        
        # Smooth the heightmap
        for _ in range(smoothing):
            heightmap = self._smooth_array(heightmap)
            
        # Normalize to 0-1
        heightmap = (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))
        return heightmap
    
    def _smooth_array(self, array, kernel_size=5):
        """Apply a simple smoothing to an array"""
        return gaussian_filter(array, sigma=kernel_size)
    
    def generate_metal_spots(self, heightmap, num_spots=20, min_distance=100):
        """Generate metal spot positions based on heightmap"""
        size = heightmap.shape[0]
        spots = []
        attempts = 0
        
        while len(spots) < num_spots and attempts < 1000:
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            
            # Check if spot is valid (not too steep, not underwater)
            if heightmap[x, y] < 0.3 or heightmap[x, y] > 0.9:
                attempts += 1
                continue
                
            # Check distance from other spots
            valid = True
            for sx, sy in spots:
                dist = np.sqrt((x-sx)**2 + (y-sy)**2)
                if dist < min_distance:
                    valid = False
                    break
            
            if valid:
                spots.append((x, y))
            
            attempts += 1
            
        return spots
    
    def save_heightmap(self, heightmap, name="map01"):
        """Save heightmap as 16-bit PNG"""
        # Scale to 16-bit
        heightmap_16bit = (heightmap * 65535).astype(np.uint16)
        img = Image.fromarray(heightmap_16bit)
        
        map_dir = os.path.join(self.output_dir, name)
        os.makedirs(map_dir, exist_ok=True)
        
        img.save(os.path.join(map_dir, "height.png"))
        return map_dir
    
    def create_map_config(self, map_dir, name, description, metal_spots):
        """Create mapinfo.lua file"""
        size = 8  # 8km map
        mapinfo_content = f"""
local mapinfo = {{
    name        = "{name}",
    shortname   = "{name}",
    description = "{description}",
    author      = "AI Map Generator",
    version     = "1",
    mapfile     = "maps/{name}.smf",
    modtype     = 3, --// 1=primary, 0=hidden, 3=map
    depend      = {{"Map Helper v1"}},
    
    maphardness     = 100,
    notDeformable   = false,
    gravity         = 130,
    tidalStrength   = 0,
    maxMetal        = 0.02,
    extractorRadius = 500,
    
    smf = {{
        minheight = 0,
        maxheight = 200,
    }},
    
    resources = {{
        resourceUnits = {{
            metal = 1000,
            energy = 1000,
        }},
    }},
    
    splats = {{
        texScales = {{0.002, 0.002, 0.002, 0.002}},
        texMults  = {{1.0, 1.0, 1.0, 1.0}},
    }},
    
    atmosphere = {{
        minWind      = 5,
        maxWind      = 25,
        fogStart     = 0.1,
        fogEnd       = 1.0,
        fogColor     = {{0.7, 0.7, 0.8}},
        skyColor     = {{0.1, 0.15, 0.7}},
        sunColor     = {{1.0, 1.0, 0.9}},
        cloudColor   = {{0.9, 0.9, 0.9}},
        cloudDensity = 0.5,
    }},
    
    terrainTypes = {{
        {{
            name = "Default",
            texture = "default.png",
            texureScale = 0.02,
        }},
    }},
    
    custom = {{
        fog = {{
            color    = {{0.26, 0.30, 0.41}},
            height   = "80%",
            fogatten = 0.003,
        }},
        precipitation = {{
            density   = 30000,
            size      = 1.5,
            speed     = 50,
            windscale = 1.2,
            texture   = 'LuaGaia/Addons/snow.png',
        }},
    }},
}}

-- Metal spot definitions
mapinfo.metalSpots = {{
"""
        
        for i, (x, y) in enumerate(metal_spots):
            # Convert to map coordinates
            map_x = (x / 1024) * size * 512
            map_z = (y / 1024) * size * 512
            mapinfo_content += f"    {{x = {map_x}, z = {map_z}}},\n"
        
        mapinfo_content += """
}

return mapinfo
"""
        
        with open(os.path.join(map_dir, "mapinfo.lua"), "w") as f:
            f.write(mapinfo_content)
    
    def generate_textures(self, heightmap, map_dir):
        """Generate basic textures based on heightmap"""
        size = heightmap.shape[0]
        
        # Generate a simple texture map
        texture = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Simple texture based on height
        for i in range(size):
            for j in range(size):
                h = heightmap[i, j]
                if h < 0.3:  # Water
                    texture[i, j] = [0, 0, 150]
                elif h < 0.4:  # Beach
                    texture[i, j] = [240, 240, 180]
                elif h < 0.7:  # Grass
                    texture[i, j] = [0, 100 + int(h * 100), 0]
                else:  # Mountain
                    texture[i, j] = [100 + int((h-0.7) * 300), 100 + int((h-0.7) * 200), 100]
        
        # Save texture
        img = Image.fromarray(texture)
        img.save(os.path.join(map_dir, "texture.png"))
        
        # Create a simple minimap
        minimap = img.resize((256, 256))
        minimap.save(os.path.join(map_dir, "minimap.png"))
    
    def create_map_archive(self, map_dir, name, install=False):
        """Create a SD7 map archive using the SD7Handler
        
        Args:
            map_dir: Directory containing the map files
            name: Name for the map
            install: Whether to install the map to the BAR maps directory
            
        Returns:
            Path to the archive directory
        """
        # Create archive directory for the extracted files
        archive_dir = os.path.join(self.output_dir, f"{name}_archive")
        os.makedirs(archive_dir, exist_ok=True)
        
        # Copy all files from map_dir to archive_dir
        for file in os.listdir(map_dir):
            shutil.copy2(os.path.join(map_dir, file), os.path.join(archive_dir, file))
        
        # Create SD7 file using the SD7Handler
        sd7_handler = SD7Handler()
        sd7_filename = os.path.join(self.output_dir, f"{name}.sd7")
        
        # Create the SD7 file
        sd7_path = sd7_handler.create_sd7(archive_dir, sd7_filename)
        
        # Install the map if requested
        if install and sd7_path:
            sd7_handler.install_map(sd7_path)
            print(f"Map installed to BAR maps directory: {name}")
        
        # Return the archive directory (for backward compatibility)
        return archive_dir
    
    def generate_complete_map(self, name="AI_Generated_Map", description="AI generated terrain", 
                             size=1024, hill_count=20, metal_spots=20):
        """Generate a complete map with all required files"""
        # Generate heightmap
        heightmap = self.generate_heightmap(size=size, hill_count=hill_count)
        
        # Generate metal spots
        spots = self.generate_metal_spots(heightmap, num_spots=metal_spots)
        
        # Save heightmap
        map_dir = self.save_heightmap(heightmap, name=name)
        
        # Create map config
        self.create_map_config(map_dir, name, description, spots)
        
        # Generate textures
        self.generate_textures(heightmap, map_dir)
        
        # Create archive
        archive_dir = self.create_map_archive(map_dir, name)
        
        return archive_dir