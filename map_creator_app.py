import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import numpy as np
from PIL import Image, ImageTk
import json
import subprocess
import sys
import pathlib # Added for Path object
import tempfile # Added for temporary directory

# Import our modules
from mapgen_core import BARMapGenerator
from ai_terrain import AITerrainGenerator
from sd7_handler import SD7Handler # Added for SD7Handler
from logger import setup_logger
from openai import APIError, AuthenticationError, RateLimitError, APIConnectionError, Timeout as OpenAITimeout # Alias Timeout

# Define the configuration file path
CONFIG_FILE_PATH = pathlib.Path.home() / ".bar_map_creator_settings.json"

def load_config():
    """Loads configuration from a JSON file."""
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                config = json.load(f)
                return config
        except (IOError, json.JSONDecodeError) as e:
            # Log this error appropriately in a real app
            print(f"Error loading config: {e}") 
            return {}
    return {}

def save_config(config_data):
    """Saves configuration to a JSON file."""
    try:
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        # Log this error appropriately
        print(f"Error saving config: {e}")

def find_bar_installation_path():
    """
    Tries to find the BAR installation directory on Windows.
    Returns the path as a string if found, otherwise None.
    """
    potential_paths = [
        pathlib.Path("C:/Program Files (x86)/Beyond All Reason"),
        pathlib.Path("C:/Program Files/Beyond All Reason"),
        pathlib.Path(os.path.expandvars('%LOCALAPPDATA%/Programs/Beyond All Reason')),
        # Add other common paths here if necessary
    ]

    # A reliable marker could be the presence of 'bar.exe' or a specific subdirectory like 'engine'
    marker_file = "bar.exe" 

    for path_candidate in potential_paths:
        if path_candidate.is_dir() and (path_candidate / marker_file).is_file():
            return str(path_candidate)
    return None

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

        # Load configuration
        self.config = load_config()
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TButton', background=self.button_color, foreground=self.text_color)
        self.style.map('TButton', background=[('active', self.accent_color)])
        
        # Initialize path variables from config or defaults
        self.output_path = tk.StringVar(value=self.config.get("output_path", os.path.abspath("generated_maps")))
        self.install_path = tk.StringVar(value=self.config.get("bar_install_path", ""))

        # Attempt to auto-detect BAR installation path if not set or invalid
        current_install_path = self.install_path.get()
        if not current_install_path or not os.path.isdir(current_install_path):
            self.logger.info("BAR installation path not configured or invalid, attempting auto-detection.")
            found_path = find_bar_installation_path()
            if found_path:
                self.logger.info(f"Auto-detected BAR installation at: {found_path}")
                self.install_path.set(found_path)
                self.config["bar_install_path"] = found_path
                save_config(self.config) # Save the auto-detected path
            else:
                self.logger.info("BAR installation path could not be auto-detected.")

        # Initialize generators
        self.map_generator = BARMapGenerator(output_dir=self.output_path.get())
        self.ai_terrain = AITerrainGenerator()

        # Initialize SD7Handler
        bar_install_dir = self.install_path.get()
        bar_maps_dir = None
        if bar_install_dir and os.path.isdir(bar_install_dir):
            bar_maps_dir = os.path.join(bar_install_dir, "data", "maps")
        
        self.sd7_handler = SD7Handler(maps_directory=bar_maps_dir,
                                      generated_maps_directory=self.output_path.get())
        
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
            import openai # Keep import here to allow for cases where openai is not installed
            import os
            from dotenv import load_dotenv
            load_dotenv() # Load variables from .env file

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                error_message = "OPENAI_API_KEY not found. Please create a '.env' file in the application's directory with your API key (e.g., OPENAI_API_KEY='your_key_here'), or set it as an environment variable."
                self.update_chat_history(f"AI Error: {error_message}\n")
                self.logger.error(error_message)
                messagebox.showerror("OpenAI Configuration Error", error_message)
                return # Stop further execution

            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4", # Consider making the model configurable
                messages=[{"role": "user", "content": prompt}]
            )
            ai_message = response.choices[0].message.content
            self.update_chat_history(f"AI: {ai_message}\n")
            self.logger.info(f"AI responded: {ai_message}")

        except AuthenticationError:
            error_message = "OpenAI API Key is invalid or you might have run out of credits. Please check your API key and OpenAI account dashboard."
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI Authentication Error", error_message)
        except RateLimitError:
            error_message = "OpenAI API rate limit exceeded. Please try again in a little while or check your usage plan."
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI Rate Limit Error", error_message)
        except APIConnectionError:
            error_message = "Could not connect to OpenAI API. Please check your internet connection."
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI Connection Error", error_message)
        except OpenAITimeout: # Using the aliased import
            error_message = "OpenAI API request timed out. This might be due to network issues or the API being slow. Please try again."
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI Timeout Error", error_message)
        except APIError as e: # Catch other OpenAI specific errors
            error_message = f"An OpenAI API error occurred: {e}"
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI API Error", error_message)
        except ValueError as e: # Catch the specific ValueError for API key missing
            error_message = str(e) # Use the message from ValueError directly
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(error_message)
            messagebox.showerror("OpenAI Configuration Error", error_message)
        except Exception as e: # General fallback
            error_message = f"An unexpected error occurred while trying to reach the AI: {e}"
            self.update_chat_history(f"AI Error: {error_message}\n")
            self.logger.error(f"OpenAI unexpected error: {e}", exc_info=True)
            messagebox.showerror("OpenAI Error", error_message)

    def listen_mic(self):
        try:
            import speech_recognition as sr
            # import pyaudio # Not strictly needed for OSError, but good for specific pyaudio errors if desired

            recognizer = sr.Recognizer()
            # Adjust recognizer sensitivity to ambient noise if needed
            # recognizer.dynamic_energy_threshold = True 
            # recognizer.pause_threshold = 0.8 # seconds of non-speaking audio before a phrase is considered complete

            with sr.Microphone() as source:
                self.update_chat_history("Listening...\n")
                self.logger.info("Microphone listening started.")
                # Adjust timeout and phrase_time_limit as needed.
                # timeout: max seconds to wait for speech before a WaitTimeoutError.
                # phrase_time_limit: max seconds a phrase can be recorded.
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                except sr.WaitTimeoutError:
                    self.update_chat_history("Mic Error: No speech detected within the time limit. Please try speaking when you click the mic button.\n")
                    self.logger.warning("Microphone WaitTimeoutError during listen.")
                    return # Exit if no speech detected

            self.update_chat_history("Processing audio...\n")
            self.logger.info("Audio captured, attempting recognition.")
            
            text = recognizer.recognize_google(audio)
            self.chat_entry.delete(0, tk.END)
            self.chat_entry.insert(0, text)
            self.update_chat_history(f"You said: {text}\n") # Clarified message
            self.logger.info(f"Microphone recognized: {text}")

        except sr.WaitTimeoutError: # This might be redundant if caught during listen, but kept for safety
            self.update_chat_history("Mic Error: No speech detected. Please try again.\n")
            self.logger.warning("Microphone WaitTimeoutError.")
        except OSError as e:
            # This can catch issues like microphone not found or access denied.
            error_message = (
                "Mic Setup Error: Microphone not found or not properly configured. "
                "Please check your system's microphone settings and permissions.\n"
            )
            self.update_chat_history(error_message)
            self.logger.error(f"Microphone OSError: {e}")
            messagebox.showerror("Mic Setup Error", "Microphone not found, not configured, or access denied. Please check system settings.")
        except sr.UnknownValueError:
            self.update_chat_history("Mic Error: Sorry, I could not understand the audio. Please try speaking clearly.\n")
            self.logger.warning("Microphone UnknownValueError.")
        except sr.RequestError as e:
            error_message = (
                f"Mic Error: Could not request results from speech recognition service; {e}. "
                "Check your internet connection.\n"
            )
            self.update_chat_history(error_message)
            self.logger.error(f"Microphone RequestError: {e}")
        except Exception as e: # General fallback for other unexpected errors
            error_message = f"Mic Error: An unexpected error occurred with speech input: {e}\n"
            self.update_chat_history(error_message)
            self.logger.error(f"Microphone unexpected error: {e}", exc_info=True) # Log with stack trace

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
        
        # self.output_path is now initialized in __init__
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, state="readonly")
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(output_frame, text="...", width=3, command=self.browse_output_and_save_config)
        browse_button.pack(side=tk.RIGHT)
        
        # Installation path
        install_frame = ttk.Frame(left_frame)
        install_frame.pack(fill=tk.X, pady=5)
        install_label = ttk.Label(install_frame, text="BAR Installation:")
        install_label.pack(side=tk.LEFT)
        
        # Try to find BAR installation
        # The application will need to implement a method to auto-detect this path 
        # or allow the user to set it. This value would then be loaded (e.g., from a config).
        # self.install_path is now initialized in __init__
        install_entry = ttk.Entry(install_frame, textvariable=self.install_path, state="readonly")
        install_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_install_button = ttk.Button(install_frame, text="...", width=3, command=self.browse_install_and_save_config)
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
    
    def browse_output_and_save_config(self):
        directory = filedialog.askdirectory(initialdir=self.output_path.get())
        if directory:
            self.output_path.set(directory)
            self.map_generator.output_dir = directory
            if hasattr(self, 'sd7_handler'): # Ensure sd7_handler exists
                self.sd7_handler.generated_maps_directory = directory
            self.config["output_path"] = directory
            save_config(self.config)
    
    def browse_install_and_save_config(self):
        directory = filedialog.askdirectory(initialdir=self.install_path.get())
        if directory:
            self.install_path.set(directory)
            self.config["bar_install_path"] = directory
            save_config(self.config)
            # Update SD7Handler's maps_directory
            if hasattr(self, 'sd7_handler'): # Ensure sd7_handler exists
                bar_maps_dir = None
                if directory and os.path.isdir(directory):
                    bar_maps_dir = os.path.join(directory, "data", "maps")
                self.sd7_handler.maps_directory = bar_maps_dir
                # Re-create relevant directories if they were None before
                if self.sd7_handler.maps_directory and isinstance(self.sd7_handler.maps_directory, (str, pathlib.Path)):
                    os.makedirs(self.sd7_handler.maps_directory, exist_ok=True)
                    self.logger.info(f"SD7Handler maps directory updated: {self.sd7_handler.maps_directory}")

    
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
        
        # Generate a preview image in the system's temporary directory
        temp_dir = tempfile.gettempdir()
        preview_file = os.path.join(temp_dir, "bar_map_preview.png")
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

if __name__ == "__main__":
    # Start the application
    root = tk.Tk()
    app = BARMapCreatorApp(root)
    # Ensure main layout is created (if not done in __init__)
    if hasattr(app, 'create_layout'):
        app.create_layout()
    root.mainloop()