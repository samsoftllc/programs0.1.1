import tkinter as tk
from tkinter import messagebox
import base64
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk, ImageFont

# ============================================================
#         macOS 2025 Ultra-Accurate Desktop Rewrite
# ============================================================
#
#  Original code by the user, updated by Gemini for
#  runnability and tkinter improvements.
#
#  Key Changes:
#  1. Added actual Base64 placeholder data for icons/wallpaper.
#  2. Removed unused imports (pygame, os, threading, etc.).
#  3. Rewrote create_desktop_icon to use canvas.create_window.
#  4. Simplified and centered the dock logic using frames.
#  5. Consolidated icon loading into a single helper function.
#
# ============================================================

# ============================================================
#                  BASE64 PLACEHOLDER ASSETS
# ============================================================
#  Generated simple placeholders to make the script runnable.

# Fallback Wallpaper (Purple/Blue Gradient)
# Force fallback by clearing the wallpaper B64
WALLPAPER_B64 = ""

# Finder Icon (Blue 'F')
FINDER_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAHSSURBVAChExOCoAMAYK2K+7/LpqYwB7tQ8wLT0lq3YwAAAAAAAAAAAAAAAAAACOB6jwB4O+Cc0gY8APAn/I61HAGvADgE0BVAnwLoAdASgEoArQKoI0A/AbwG4BaABQBvANoA8BpAXgA4AUAHgK4A6gBQB8BSAMIBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAAAAAAAAAAAAAAAAAAYB4/9l0Bls0Y2mQAAAAASUVORK5CYII="

# VSCode Icon (Blue 'V')
VSCODE_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAHOSURBVAChExOClwEAYK2K+7+XTRMuYTc0/wVzEtp61Y4BAAAAAAAAAAAAAAAAAAAAwHl9jwB4W+Cc0gY8APAn/I61HAGvADgE0BVAnwLoAdASgEoArQKoI0A/AbwG4BaABQBvANoA8BpAXgA4AUAHgK4A6gBQB8BSAMIBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAskNkA+E8AfgDkAYATADoAdAVQBwB1AFgKAMMBVAcwGkBLANoAUAfAUgBgBIA0AEoAaAPAFIA/AfwEcB0gDUAvgKkALAFAFQBdANQBYCWAFAAAAAAAAAAAAAAAAAAAYB5/XfAAZwpO4Y0AAAAASUVORK5CYII="

# Launchpad Icon (Red 'L')
LAUNCHPAD_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAHTSURBVAChExOCwAEAYK2i+7+XbXAhCyE/YB5CW2/qDAAAAAAAAAAAAAAAAAAAAPB/eI8AeGvgXNIAPADwJ/yOtRwBrwAcAmgKoE8B9ACgJACVAFAKgDYB6BOAfgB4DcAtAAuANIBeAF4AOAHgAIAjAFUAqANAPwBsBSAMAOoA5gBQCwBaANAOgLUAkAcATQGgDYB5AP4E8BNAbQBTAH0ApgKQCgCqANAOgMIAUgCwBGY7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1IcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1IcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1AcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AAAAAAAAAAAAAAAAAAAAwIw+380D48A5/IYAAAAASUVORK5CYII="

# Settings Icon (Gray 'S')
SETTINGS_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAHESURBVAChExOClgEAYK2K+7+XbWwhN3QeMDeBtt7UHQMAAAAAAAAAAAAAAAAAAADge7xHALS3wDmlDXgA4E/4HWs5Al4BOATQFUCPAugBQEsAKAWAWgHUBaCfgF4DuAWgAMC7QBsAegWgFwBOAOAA0BVAFQBqAKgHYCsAwwGqAxgNIAWANABqAKAWAHIAYASANABKAGgDwCmAfgL4CWA7gDSAvgCmAlAKgKkAdAOgDgA7AbQEZjsAfgL4AZAOAE4AOADgCKAKAGUA1ABQDoCtAwwHUB3AaAClAWADgJoAZAWAGAAkAKQCaANAHgE8A/QTQGkAdgL4ApgKgVACqAtANGKsBYCWArQJmOwB+AvEBIB0AnAA4AOAIIAqAMgDqAVAPgK0ADAdQHYDRACQNYAMAawGQFQBiAJAAkAKgDQCPAH4C+AmgNYA6AH0BpgKgVAKqAtANGKsBYCWArQJmOwB+AvEBIB0AnAA4AOAIIAqAMgDqAVAPgK0ADAdQHYDRACQNYAMAawGQFQBiAJAAkAKgDQCPAH4C+AmgNYA6AH0BpgKgVAKqAtANGKsBYCWArQJmOwB+AvEBIB0AnAA4AOAIIAqAMgDqAVAPgK0ADAdQHYDRACQNYAMAawGQFQBiAJAAkAKgDQCPAH4C+AmgNYA6AH0BpgKgVAKqAtANGKsBYCWArQJmOwB+AvEBIB0AnAA4AOAIIAqAMgDqAVAPgK0ADAdQHYDRACQNYAMAawGQFQBiAJAAkAKgDQCPAH4C+AmgNYA6AH0BpgKgVAKqAtANGKsBYCWArQJmOwB+AvEBIB0AnAA4AOAIIAqAMgDqAVAPgK0ADAdQHYDRACQNYAMAawGQFQBiAJAAkAKgDQCPAH4C+AmgNYA6AH0BpgKgVAKqAtANGKsBYCWArQJmOwAAAAAAAAAAAAAAAAAAYB4/ZPYDxEWiA4sAAAAASUVORK5CYII="

# Trash Icon (Red 'T')
TRASH_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAHQSURBVAChExOCwAEAYK2i+7+XbXAhCyE/YB5CW2/qDAAAAAAAAAAAAAAAAAAAAPB/eI8AeGvgXNIAPADwJ/yOtRwBrwAcAmgKoE8B9ACgJACVAFAKgDYB6BOAfgB4DcAtAAuANIBeAF4AOAHgAIAjAFUAqANAPwBsBSAMAOoA5gBQCwBaANAOgLUAkAcATQGgDYB5AP4E8BNAbQBTAH0ApgKQCgCqANAOgMIAUgCwBGY7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1IcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1IcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AH4C+AGQDgBOAOAAgCMAVQCoQ0A/A2ArAIMB1AcZD0BLAFoA0A6AtQAgDwCaAkAbAPMA/AngJ4DaAKYA+gBMBSCVAKgCYDoAhQFIAcAimO0A+AlgB0A6ADgB4ACAIwBVAKhDQD8DbCsAwwHUhxl7QFsA0AKEfQAoBcBWAGQHAE0BoA2AeQD+BPATQG0AUwB9AKYCUCoAqAJgOgCFAUjFfQAshGk7AAAAAAAAAAAAAAAAAAAAwIw+380D48A5/IYAAAAASUVORK5CYII="


# ============================================================
#                      HELPER FUNCTIONS
# ============================================================

def create_hdr_wallpaper_pil(width, height):
    """Create a fallback 'HDR' gradient wallpaper using PIL."""
    img = Image.new('RGB', (width, height), color='#ff8a00')
    draw = ImageDraw.Draw(img)
    
    # Simple vertical gradient - Bright Orange to Hot Pink
    for i in range(height):
        # Gradient from #ff8a00 to #e52e71
        r = int(255 + (i / height) * (229 - 255))
        g = int(138 + (i / height) * (46 - 138))
        b = int(0 + (i / height) * (113 - 0))
        color = (r, g, b)
        draw.line([(0, i), (width, i)], fill=color)
    
    return ImageTk.PhotoImage(img)

def scale_wallpaper_pil(image_data, screen_w, screen_h):
    """Resize wallpaper using PIL for better quality."""
    try:
        img_data = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_data))
        
        # Calculate aspect fill
        iw, ih = img.size
        scale = max(screen_w / iw, screen_h / ih)
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = (new_w - screen_w) / 2
        top = (new_h - screen_h) / 2
        right = (new_w + screen_w) / 2
        bottom = (new_h + screen_h) / 2
        
        img = img.crop((left, top, right, bottom))
        
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading wallpaper: {e}")
        # Create a fallback gradient wallpaper
        return create_hdr_wallpaper_pil(screen_w, screen_h)

def create_placeholder_icon_pil(size=64, color="#007AFF", text=""):
    """Create a placeholder icon using PIL."""
    try:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle
        draw.rounded_rectangle([0, 0, size, size], 
                             radius=size//5, fill=color)
        
        # Try to add text
        try:
            # Use a basic, commonly available font
            font = ImageFont.truetype("Arial", size//2)
        except:
            font = ImageFont.load_default()
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        draw.text((x, y), text, fill="white", font=font)
            
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error creating placeholder icon: {e}")
        # Fallback to a simple PhotoImage
        photo = tk.PhotoImage(width=size, height=size)
        photo.put(color, to=(0, 0, size, size))
        return photo

def load_icon(b64_data, size=64, fallback_color="#007AFF", fallback_text="?"):
    """Loads an icon from Base64 or creates a fallback."""
    if b64_data:
        try:
            img_data = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading icon from Base64: {e}")
            pass
    
    # Fallback if load fails or no data
    return create_placeholder_icon_pil(size, fallback_color, fallback_text)


# Application window management
def open_app_window(root, app_name, app_type=None):
    """Open an application window."""
    window = tk.Toplevel(root)
    window.title(app_name)
    window.geometry("800x600")
    window.configure(bg='#ffffff')
    
    # --- Custom Title Bar ---
    # This frame mimics the macOS title bar
    title_bar = tk.Frame(window, bg='#e8e8e8', height=35, relief='flat', bd=0)
    title_bar.pack(fill='x', side='top')

    # Window buttons (close, minimize, maximize)
    btn_frame = tk.Frame(title_bar, bg='#e8e8e8')
    btn_frame.pack(side='left', padx=10, pady=5)
    
    btn_close = tk.Button(btn_frame, text="●", fg="#ff5f57", bg='#e8e8e8', 
                         bd=0, font=("Arial", 12), command=window.destroy)
    btn_minimize = tk.Button(btn_frame, text="●", fg="#ffbd2e", bg='#e8e8e8', 
                           bd=0, font=("Arial", 12), command=window.iconify)
    btn_maximize = tk.Button(btn_frame, text="●", fg="#28c940", bg='#e8e8e8', 
                           bd=0, font=("Arial", 12))
    
    btn_close.pack(side='left', padx=2)
    btn_minimize.pack(side='left', padx=2)
    btn_maximize.pack(side='left', padx=2)
    
    # Window Title
    title_label = tk.Label(title_bar, text=app_name, bg='#e8e8e8', fg='#333333',
                           font=("SF Pro Display", 14, "bold"))
    title_label.pack(side='left', expand=True)

    # Make the title bar draggable
    def on_press(event):
        window.x = event.x
        window.y = event.y

    def on_drag(event):
        deltax = event.x - window.x
        deltay = event.y - window.y
        x = window.winfo_x() + deltax
        y = window.winfo_y() + deltay
        window.geometry(f"+{x}+{y}")

    title_bar.bind("<ButtonPress-1>", on_press)
    title_bar.bind("<B1-Motion>", on_drag)
    title_label.bind("<ButtonPress-1>", on_press)
    title_label.bind("<B1-Motion>", on_drag)

    # --- End Custom Title Bar ---

    # App content
    content_frame = tk.Frame(window, bg='#ffffff')
    content_frame.pack(fill='both', expand=True)
    
    if app_name == "Finder":
        # Simple finder-like content
        sidebar = tk.Frame(content_frame, bg='#f0f0f0', width=150)
        sidebar.pack(side='left', fill='y')
        
        main_content = tk.Frame(content_frame, bg='#ffffff')
        main_content.pack(side='right', fill='both', expand=True, padx=20, pady=20)
        
        label = tk.Label(sidebar, text="Favorites\n\nDocuments\nDownloads\nApplications\nDesktop", 
                         font=("SF Pro Display", 14), bg='#f0f0f0', justify='left',
                         padx=10, pady=10, anchor='nw')
        label.pack()
        
        files_label = tk.Label(main_content, text="Item 1\nItem 2\nItem 3",
                               font=("SF Pro Display", 16), bg='#ffffff', justify='left')
        files_label.pack(anchor='nw')
        
    elif app_name == "Settings":
        # Simple settings-like content
        settings_label = tk.Label(content_frame, text="Wi-Fi\n\nBluetooth\n\nDisplay\n\nSound", 
                                 font=("SF Pro Display", 18), bg='#ffffff', justify='left')
        settings_label.pack(pady=50, padx=50, anchor='nw')
    else:
        # Default content
        label = tk.Label(content_frame, text=f"Welcome to {app_name}", 
                        font=("SF Pro Display", 24), bg='#ffffff')
        label.pack(pady=50)
    
    # Remove the default OS title bar
    try:
        window.overrideredirect(True)
    except tk.TclError:
        print("Could not remove OS title bar (may not work on all platforms).")
        window.overrideredirect(False) # Fallback

    return window

# Bouncing hover effect
def icon_hover(event):
    """Handle icon hover animation."""
    widget = event.widget
    widget.config(pady=0) # Move up

def icon_leave(event):
    """Handle icon leave animation."""
    widget = event.widget
    widget.config(pady=10) # Move back down


# Dock button creator
def add_dock_icon(parent, img, command):
    """Add an icon to the dock."""
    # Use a Label as the button
    btn = tk.Label(parent, image=img, bg="#dcdcdc", bd=0, 
                   cursor="hand2", pady=10)
    btn.pack(side='left', padx=10)
    
    btn.image = img  # Keep a reference
    
    btn.bind("<Enter>", icon_hover)
    btn.bind("<Leave>", icon_leave)
    btn.bind("<Button-1>", lambda e: command())
    return btn

def create_desktop_icon(parent_canvas, text, x, y, icon_img, command):
    """Create a desktop icon on the canvas."""
    
    # --- This is a workaround for tkinter canvas transparency ---
    # We create a frame, put the icon and text in it, and
    # place the *frame* on the canvas.
    
    icon_frame = tk.Frame(parent_canvas, bg="#ffffff", bd=0)
    # Set a semi-transparent background color to simulate frosting
    icon_frame.config(bg_color='#ffffff') 
    
    try:
        # This is a bit of a hack for semi-transparency on frames
        # It won't work on all systems.
        parent_canvas.master.attributes("-alpha", 0.9)
    except:
        pass # Will fail on non-Windows
        
    # Use a Label, not a Button, for the icon image
    icon_label = tk.Label(icon_frame, image=icon_img, bg="#ffffff", cursor="hand2")
    icon_label.pack(pady=(5, 2))
    icon_label.image = icon_img
    
    text_label = tk.Label(icon_frame, text=text, bg="#ffffff", fg='black', 
                         font=("SF Pro Text", 12), cursor="hand2")
    text_label.pack(pady=(2, 5))
    
    # Bind clicks on all elements to the command
    icon_frame.bind("<Button-1>", lambda e: command())
    icon_label.bind("<Button-1>", lambda e: command())
    text_label.bind("<Button-1>", lambda e: command())
    
    # Place the frame on the canvas
    parent_canvas.create_window(x, y, window=icon_frame, anchor="n")
    return icon_frame

# ============================================================
#                      MAIN WINDOW INIT
# ============================================================

root = tk.Tk()
root.title("macOS Simulator 2025")

# Set fixed window size
window_width = 600
window_height = 400

# Get screen dimensions to center the window
screen_width  = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x_center = (screen_width // 2) - (window_width // 2)
y_center = (screen_height // 2) - (window_height // 2)

root.geometry(f"{window_width}x{window_height}+{x_center}+{y_center}")

# Remove borderless mode to show standard window
# try:
#     root.overrideredirect(True)
# except tk.TclError:
#     print("Warning: Could not remove window borders.")


# ============================================================
#                   LOAD / SCALE WALLPAPER
# ============================================================

wallpaper_image = scale_wallpaper_pil(
    WALLPAPER_B64,
    window_width,
    window_height
)

# Load icons
icon_size = 56 # Dock icon size
finder_icon = load_icon(FINDER_ICON_B64, icon_size, "#007AFF", "F")
launchpad_icon = load_icon(LAUNCHPAD_ICON_B64, icon_size, "#FF2D55", "L")
vscode_icon = load_icon(VSCODE_ICON_B64, icon_size, "#007ACC", "V")
settings_icon = load_icon(SETTINGS_ICON_B64, icon_size, "#8E8E93", "S")
trash_icon = load_icon(TRASH_ICON_B64, icon_size, "#FF3B30", "T")

# Desktop icon size
desktop_icon_size = 64
finder_icon_desktop = load_icon(FINDER_ICON_B64, desktop_icon_size, "#007AFF", "F")
vscode_icon_desktop = load_icon(VSCODE_ICON_B64, desktop_icon_size, "#007ACC", "V")
settings_icon_desktop = load_icon(SETTINGS_ICON_B64, desktop_icon_size, "#8E8E93", "S")


# Draw desktop canvas
desktop = tk.Canvas(
    root,
    width=window_width,
    height=window_height,
    highlightthickness=0,
    bd=0
)
desktop.place(x=0, y=0)
desktop.create_image(window_width//2, window_height//2, image=wallpaper_image, anchor="center")

# ============================================================
#                       TOP MENU BAR
# ============================================================

# Use a semi-transparent color for the menu bar
menu_bar = tk.Frame(root, bg="#1c1c1e", height=28)
menu_bar.place(x=0, y=0, relwidth=1)

menu_left = tk.Label(
    menu_bar,
    text="    Finder     File     Edit     View     Go     Window     Help",
    fg="white",
    bg="#1c1c1e",
    font=("SF Pro Display", 13),
    anchor='w'
)
menu_left.pack(side="left", padx=15)

clock_label = tk.Label(
    menu_bar,
    fg="white",
    bg="#1c1c1e",
    font=("SF Pro Text", 13)
)
clock_label.pack(side="right", padx=20)

def update_clock():
    """Update the clock display."""
    clock_label.config(text=datetime.now().strftime("%a %b %d   %I:%M %p"))
    root.after(1000, update_clock)

update_clock()

# ============================================================
#                           DOCK
# ============================================================

# A frame to hold the dock, placed at the bottom
dock_container = tk.Frame(root, bg='', bd=0) # Transparent background
# This frame will auto-size to its children
dock_container.pack(side="bottom", pady=10)

# The dock itself, with a rounded-corner-like background
dock_bg = tk.Frame(
    dock_container, 
    bg="#dcdcdc",  # Light gray, semi-transparent-like
    bd=1, 
    relief='raised'
)
dock_bg.pack()

# Add icons to the dock_bg frame
finder_btn = add_dock_icon(dock_bg, finder_icon, 
                          lambda: open_app_window(root, "Finder"))
launchpad_btn = add_dock_icon(dock_bg, launchpad_icon, 
                             lambda: open_app_window(root, "Launchpad"))
vscode_btn = add_dock_icon(dock_bg, vscode_icon, 
                          lambda: open_app_window(root, "VS Code"))
settings_btn = add_dock_icon(dock_bg, settings_icon, 
                            lambda: open_app_window(root, "Settings"))
trash_btn = add_dock_icon(dock_bg, trash_icon, 
                         lambda: open_app_window(root, "Trash"))


# ============================================================
#                     DESKTOP ICONS
# ============================================================

# Create desktop icons, adjusting coordinates for 600x400 window
try:
    create_desktop_icon(desktop, "Applications", window_width - 100, 80, finder_icon_desktop,
                        lambda: open_app_window(root, "Finder"))
    create_desktop_icon(desktop, "My Project", window_width - 100, 200, vscode_icon_desktop,
                        lambda: open_app_window(root, "VS Code"))
    create_desktop_icon(desktop, "Settings", window_width - 100, 320, settings_icon_desktop,
                        lambda: open_app_window(root, "Settings"))
except Exception as e:
    print(f"Could not create desktop icons: {e}")

# ============================================================
#                     WINDOW MANAGEMENT
# ============================================================

def minimize_all():
    """Minimize all windows."""
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.iconify()

def show_desktop():
    """Show desktop by minimizing all windows."""
    minimize_all()

# Add global keyboard shortcuts
# Use 'Control' for cross-platform compatibility
root.bind('<Control-m>', lambda e: minimize_all())
root.bind('<Control-d>', lambda e: show_desktop())

# ============================================================
#                     QUIT FUNCTIONALITY
# ============================================================

def quit_app():
    """Quit the application."""
    if messagebox.askokcancel("Quit", "Are you sure you want to shut down?"):
        root.quit()
        root.destroy()

# Add quit to menu (simulated)
# Use 'Control-q' and 'Escape' for cross-platform
root.bind('<Control-q>', lambda e: quit_app())
root.bind('<Escape>', lambda e: quit_app())

# ============================================================
#                     MAIN LOOP
# ============================================================

if __name__ == "__main__":
    try:
        print("macOS Simulator 2025 starting...")
        print("Press Ctrl+Q or Esc to quit")
        root.mainloop()
    except KeyboardInterrupt:
        print("Shutting down...")
        if root:
            root.quit()
            root.destroy()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if root:
            root.quit()
            root.destroy()
