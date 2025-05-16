import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import numpy as np
from PIL import Image, ImageTk
import json
import subprocess
import sys

# Import our modules
from mapgen_core import BARMapGenerator
from ai_terrain import AITerrainGenerator

from logger import setup_logger

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class BARMapCreatorApp:
    def __init__(self, root):
        self.logger = setup_logger()
        self.logger.info("App started.")
        self.root = root
        self.root.title("Beyond All Reason - AI Map Creator")

        # Tooltips dictionary for later reference
        self.tooltips = {}
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set dark theme colors
        self.bg_color = "#1B2838"  # Dark navy
        self.text_color = "#CCCCCC"  # Light gray
        self.accent_color = "#FF6B00"  # Bright orange
        self.button_color = "#2A3F5A"  # Medium navy
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TButton', background=self.button_color, foreground=self.text_color)
        self.style.map('TButton', background=[('active', self.accent_color)])
        
        # Initialize generators
        self.map_generator = BARMapGenerator(output_dir="generated_maps")
        self.ai_terrain = AITerrainGenerator()
        
        # Map settings
        self.map_name = tk.StringVar(value="AI_Generated_Map")
        self.map_description = tk.StringVar(value="AI generated terrain for Beyond All Reason")
        self.map_size = tk.IntVar(value=8)  # in km
        self.terrain_type = tk.StringVar(value="random")
        self.metal_spots = tk.IntVar(value=20)
        self.hill_count = tk.IntVar(value=20)
        self.random_seed = tk.IntVar(value=42)
        self.use_random_seed = tk.BooleanVar(value=True)

        # Help text for tooltips
        self.help_texts = {
            'map_name': "Enter a unique name for your map.",
            'map_description': "Describe your map for easy identification.",
            'map_size': "Set the map size in kilometers (4-64).",
            'terrain_type': "Choose the type of terrain to generate.",
            'metal_spots': "Number of metal spots to place on the map (0-200).",
            'hill_count': "Number of hills to generate (0-200).",
            'random_seed': "Set a seed for reproducible results.",
            'use_random_seed': "Toggle to use a random seed or specify your own.",
            'install_to_bar': "Install map to BAR after creation.",
            'generate_preview': "Generate a preview of your map.",
            'create_map': "Create and save the map files.",
            'unpack_sd7': "Unpack an SD7 map archive (coming soon).",
            'edit_sd7': "Edit an existing SD7 map (coming soon).",
            'verify_md5': "Verify the MD5 checksum of a map (coming soon).",
            'batch_process': "Batch process multiple maps (coming soon).",
            'output_dir': "Directory where generated maps will be saved.",
            'bar_install': "Location of your BAR installation.",
            'chatbox': "Ask for help, suggestions, or design changes. Use the mic to dictate.",
        }
        
        # Current map data
        self.current_heightmap = None
        self.current_preview_image = None

        # --- Chatbox for OpenAI interaction and error feedback ---
        self.chat_frame = ttk.Frame(self.root)
        self.chat_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        self.chat_history = tk.Text(self.chat_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ToolTip(self.chat_history, self.help_texts['chatbox'])

        self.chat_entry = tk.Entry(self.chat_frame)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.chat_entry.bind('<Return>', lambda e: self.send_chat())
        ToolTip(self.chat_entry, self.help_texts['chatbox'])

        self.mic_button = ttk.Button(self.chat_frame, text="🎤", command=self.listen_mic)
        self.mic_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.mic_button, "Click to use your microphone for chat input.")

        self.send_button = ttk.Button(self.chat_frame, text="Send", command=self.send_chat)
        self.send_button.pack(side=tk.LEFT)
        ToolTip(self.send_button, "Send your chat message to the AI assistant.")

    def send_chat(self):
        user_message = self.chat_entry.get()
        if not user_message.strip():
            return
        self.update_chat_history(f"You: {user_message}\n")
        self.logger.info(f"User chat input: {user_message}")
        self.chat_entry.delete(0, tk.END)
        threading.Thread(target=self.ask_openai, args=(user_message,)).start()

    def update_chat_history(self, message):
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, message)
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)
        self.logger.info(f"Chat history updated: {message.strip()}")

    def ask_openai(self, prompt):
        try:
            import openai
            import os
            from dotenv import load_dotenv
            load_dotenv()
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            ai_message = response.choices[0].message['content']
            self.update_chat_history(f"AI: {ai_message}\n")
            self.logger.info(f"AI responded: {ai_message}")
        except Exception as e:
            self.update_chat_history(f"AI Error: {e}\n")
            self.logger.error(f"OpenAI Error: {e}")
            messagebox.showerror("OpenAI Error", str(e))

    def listen_mic(self):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.update_chat_history("Listening...\n")
                self.logger.info("Microphone listening started.")
                audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                self.chat_entry.delete(0, tk.END)
                self.chat_entry.insert(0, text)
                self.update_chat_history(f"(Recognized) {text}\n")
                self.logger.info(f"Microphone recognized: {text}")
            except Exception as e:
                self.update_chat_history(f"Mic Error: {e}\n")
                self.logger.error(f"Microphone recognition error: {e}")
                messagebox.showerror("Mic Error", str(e))
        except Exception as e:
            self.update_chat_history(f"Mic Setup Error: {e}\n")
            self.logger.error(f"Microphone setup error: {e}")
            messagebox.showerror("Mic Setup Error", str(e))

    def validate_map_settings(self):
        if self.map_size.get() < 4 or self.map_size.get() > 64:
            messagebox.showwarning("Invalid Map Size", "Map size must be between 4 and 64 km.")
            self.logger.warning("Invalid map size input.")
            return False
        if self.metal_spots.get() < 0 or self.metal_spots.get() > 200:
            messagebox.showwarning("Invalid Metal Spots", "Metal spots must be between 0 and 200.")
            self.logger.warning("Invalid metal spots input.")
            return False
        if self.hill_count.get() < 0 or self.hill_count.get() > 200:
            messagebox.showwarning("Invalid Hill Count", "Hill count must be between 0 and 200.")
            self.logger.warning("Invalid hill count input.")
            return False
        return True

    # Example: Call this before generating a preview or map
    def generate_preview(self):
        if not self.validate_map_settings():
            return
        try:
            # ... existing preview logic ...
            self.logger.info("Preview generated.")
            pass
        except Exception as e:
            self.update_chat_history(f"Preview Error: {e}\n")
            self.logger.error(f"Preview generation error: {e}")
            messagebox.showerror("Preview Error", str(e))

    def create_map(self):
        if not self.validate_map_settings():
            return
        try:
            # ... existing map creation logic ...
            self.logger.info("Map created.")
            pass
        except Exception as e:
            self.update_chat_history(f"Map Creation Error: {e}\n")
            self.logger.error(f"Map creation error: {e}")
            messagebox.showerror("Map Creation Error", str(e))
eate the main layout
        self.create_layout()
        
        # Initialize preview
        self.generate_preview()
    
    def create_layout(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel (settings)
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Settings header
        settings_label = ttk.Label(left_frame, text="Map Settings", font=("Arial", 14, "bold"))
        settings_label.pack(pady=(0, 10), anchor=tk.W)
        
        # Map name
        name_frame = ttk.Frame(left_frame)
        name_frame.pack(fill=tk.X, pady=5)
        name_label = ttk.Label(name_frame, text="Map Name:")
        name_label.pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame, textvariable=self.map_name)
        name_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Map description
        desc_frame = ttk.Frame(left_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        desc_label = ttk.Label(desc_frame, text="Description:")
        desc_label.pack(side=tk.LEFT)
        desc_entry = ttk.Entry(desc_frame, textvariable=self.map_description)
        desc_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Map size
        size_frame = ttk.Frame(left_frame)
        size_frame.pack(fill=tk.X, pady=5)
        size_label = ttk.Label(size_frame, text="Map Size (km):")
        size_label.pack(side=tk.LEFT)
        size_options = [4, 8, 10, 12, 16, 20]
        size_dropdown = ttk.Combobox(size_frame, textvariable=self.map_size, values=size_options, state="readonly")
        size_dropdown.pack(side=tk.RIGHT)
        
        # Terrain type
        terrain_frame = ttk.Frame(left_frame)
        terrain_frame.pack(fill=tk.X, pady=5)
        terrain_label = ttk.Label(terrain_frame, text="Terrain Type:")
        terrain_label.pack(side=tk.LEFT)
        terrain_options = ["random", "mountain_range", "river_valley", "plateau", "crater", "hills", "archipelago"]
        terrain_dropdown = ttk.Combobox(terrain_frame, textvariable=self.terrain_type, values=terrain_options, state="readonly")
        terrain_dropdown.pack(side=tk.RIGHT)
        
        # Metal spots
        metal_frame = ttk.Frame(left_frame)
        metal_frame.pack(fill=tk.X, pady=5)
        metal_label = ttk.Label(metal_frame, text="Metal Spots:")
        metal_label.pack(side=tk.LEFT)
        metal_scale = ttk.Scale(metal_frame, from_=5, to=40, variable=self.metal_spots, orient=tk.HORIZONTAL)
        metal_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        metal_value = ttk.Label(metal_frame, textvariable=self.metal_spots)
        metal_value.pack(side=tk.RIGHT, padx=5)
        
        # Hill count
        hill_frame = ttk.Frame(left_frame)
        hill_frame.pack(fill=tk.X, pady=5)
        hill_label = ttk.Label(hill_frame, text="Hill Count:")
        hill_label.pack(side=tk.LEFT)
        hill_scale = ttk.Scale(hill_frame, from_=5, to=40, variable=self.hill_count, orient=tk.HORIZONTAL)
        hill_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        hill_value = ttk.Label(hill_frame, textvariable=self.hill_count)
        hill_value.pack(side=tk.RIGHT, padx=5)
        
        # Random seed
        seed_frame = ttk.Frame(left_frame)
        seed_frame.pack(fill=tk.X, pady=5)
        seed_check = ttk.Checkbutton(seed_frame, text="Use Random Seed", variable=self.use_random_seed)
        seed_check.pack(side=tk.LEFT)
        seed_entry = ttk.Entry(seed_frame, textvariable=self.random_seed, width=10)
        seed_entry.pack(side=tk.RIGHT)
        
        # Action buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Checkbox for installing map directly to BAR maps directory
        self.install_to_bar = tk.BooleanVar(value=False)
        install_checkbox = ttk.Checkbutton(button_frame, text="Install to BAR after creation", variable=self.install_to_bar)
        install_checkbox.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        preview_button = ttk.Button(button_frame, text="Generate Preview", command=self.generate_preview)
        preview_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        create_button = ttk.Button(button_frame, text="Create Map", command=self.create_map)
        create_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # Placeholder for future SD7 handler features
        sd7_frame = ttk.LabelFrame(left_frame, text="SD7 Tools (Coming Soon)")
        sd7_frame.pack(fill=tk.X, pady=10)
        ttk.Button(sd7_frame, text="Unpack SD7", state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(sd7_frame, text="Edit SD7", state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(sd7_frame, text="Verify MD5", state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(sd7_frame, text="Batch Process", state=tk.DISABLED).pack(fill=tk.X, pady=2)
        
        # Output directory
        output_frame = ttk.Frame(left_frame)
        output_frame.pack(fill=tk.X, pady=10)
        output_label = ttk.Label(output_frame, text="Output Directory:")
        output_label.pack(side=tk.LEFT)
        
        self.output_path = tk.StringVar(value=os.path.abspath("generated_maps"))
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, state="readonly")
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(output_frame, text="...", width=3, command=self.browse_output)
        browse_button.pack(side=tk.RIGHT)
        
        # Installation path
        install_frame = ttk.Frame(left_frame)
        install_frame.pack(fill=tk.X, pady=5)
        install_label = ttk.Label(install_frame, text="BAR Installation:")
        install_label.pack(side=tk.LEFT)
        
        # Try to find BAR installation
        default_path = "C:/Users/Admin/AppData/Local/Programs/Beyond-All-Reason"
        if not os.path.exists(default_path):
            default_path = ""
        
        self.install_path = tk.StringVar(value=default_path)
        install_entry = ttk.Entry(install_frame, textvariable=self.install_path, state="readonly")
        install_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_install_button = ttk.Button(install_frame, text="...", width=3, command=self.browse_install)
        browse_install_button.pack(side=tk.RIGHT)
        
        # Right panel (preview)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Preview header
        preview_label = ttk.Label(right_frame, text="Map Preview", font=("Arial", 14, "bold"))
        preview_label.pack(pady=(0, 10))
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(right_frame, bg="#000000", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_output(self):
        directory = filedialog.askdirectory(initialdir=self.output_path.get())
        if directory:
            self.output_path.set(directory)
            self.map_generator.output_dir = directory
    
    def browse_install(self):
        directory = filedialog.askdirectory(initialdir=self.install_path.get())
        if directory:
            self.install_path.set(directory)
    
    def generate_preview(self):
        self.status_var.set("Generating preview...")
        self.root.update_idletasks()
        
        # Generate heightmap using AI terrain generator
        seed = None if self.use_random_seed.get() else self.random_seed.get()
        heightmap, terrain_type = self.ai_terrain.generate_terrain(
            size=1024, 
            terrain_type=self.terrain_type.get(),
            seed=seed
        )
        
        # Store the heightmap for later use
        self.current_heightmap = heightmap
        
        # Generate a preview image
        preview_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview.png")
        self.ai_terrain.save_preview(heightmap, preview_file)
        
        # Display the preview
        self.display_preview(preview_file)
        
        self.status_var.set(f"Preview generated - Terrain type: {terrain_type}")
    
    def display_preview(self, image_path):
        # Load the image
        img = Image.open(image_path)
        
        # Resize to fit the canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet sized, use default size
            canvas_width = 500
            canvas_height = 500
        
        img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Store reference to prevent garbage collection
        self.current_preview_image = photo
        
        # Clear canvas and display image
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
    
    def create_map(self):
        if not self.current_heightmap is not None:
            messagebox.showerror("Error", "Please generate a preview first")
            return
        
        # Check if output directory exists
        output_dir = self.output_path.get()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output directory: {e}")
                return
        
        # Start map generation in a separate thread
        self.status_var.set("Creating map... This may take a while")
        self.root.update_idletasks()
        
        thread = threading.Thread(target=self._create_map_thread)
        thread.daemon = True
        thread.start()
    
    def _create_map_thread(self):
        try:
            # Generate the complete map
            map_name = self.map_name.get()
            description = self.map_description.get()
            metal_spots = self.metal_spots.get()

            # Use the already generated heightmap
            heightmap = self.current_heightmap

            # Save heightmap
            map_dir = self.map_generator.save_heightmap(heightmap, name=map_name)

            # Generate metal spots
            spots = self.map_generator.generate_metal_spots(heightmap, num_spots=metal_spots)

            # Create map config
            self.map_generator.create_map_config(map_dir, map_name, description, spots)

            # Generate textures
            self.map_generator.generate_textures(heightmap, map_dir)

            # Create archive, pass install option
            install_to_bar = self.install_to_bar.get()
            archive_dir = self.map_generator.create_map_archive(map_dir, map_name, install=install_to_bar)

            # Update status
            if install_to_bar:
                status_msg = f"Map created and installed to BAR maps directory!"
                info_msg = (
                    f"Map created and installed to BAR!\n\nFiles are in: {archive_dir}\n\n"
                    f"The map is now available in your BAR game.")
            else:
                status_msg = f"Map created successfully in {archive_dir}"
                info_msg = (
                    f"Map created successfully!\n\nFiles are in: {archive_dir}\n\n"
                    f"To use this map in Beyond All Reason, copy the files to your BAR maps directory.")

            self.root.after(0, lambda: self.status_var.set(status_msg))
            self.root.after(0, lambda: messagebox.showinfo("Success", info_msg))

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error creating map: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to create map: {e}"))

# Create requirements.txt file
def create_requirements():
    requirements = [
        "numpy",
        "pillow",
        "scipy"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))

# Create README file
def create_readme():
    readme_content = """# Beyond All Reason - AI Map Creator

A simple AI-powered map generator for Beyond All Reason.

## Features

- AI-generated terrain patterns
- Customizable map settings
- Preview generation
- Complete map file creation

## Requirements

- Python 3.7+
- Required packages (install with `pip install -r requirements.txt`):
  - numpy
  - pillow
  - scipy

## Usage

1. Run `python map_creator_app.py`
2. Configure map settings
3. Generate a preview
4. Create the map
5. Copy the generated files to your BAR maps directory

## Map Types

- Mountain Range: Creates mountain ridges with peaks
- River Valley: Creates a river valley with surrounding terrain
- Plateau: Creates elevated flat areas with cliff edges
- Crater: Creates a terrain with multiple impact craters
- Hills: Creates a natural hilly terrain
- Archipelago: Creates islands surrounded by water

## Installation

```
pip install -r requirements.txt
python map_creator_app.py
```

## Notes

This tool generates map files compatible with Beyond All Reason. To use the generated maps:

1. Copy the files from the output directory to your BAR maps directory
2. The maps will appear in the game's map selection menu

## Credits

Created with AI assistance for Beyond All Reason community.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)

# Create startup script
def create_startup_script():
    bat_content = """@echo off
echo Starting BAR Map Creator...
python map_creator_app.py
pause
"""
    
    with open("start_map_creator.bat", "w") as f:
        f.write(bat_content)

if __name__ == "__main__":
    # Create supporting files
    create_requirements()
    create_readme()
    create_startup_script()
    
    # Start the application
    root = tk.Tk()
    app = BARMapCreatorApp(root)
    root.mainloop()