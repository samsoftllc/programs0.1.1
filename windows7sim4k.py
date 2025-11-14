import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime
import platform  # For OS detection

class Win7Simulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows 7 Simulation")
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Hide the main window initially
        self.root.withdraw()
        
        # Run the boot sequence first
        self.run_boot_sequence()
        
        self.root.mainloop()

    def run_boot_sequence(self):
        """Creates a modal boot screen with a progress bar."""
        self.boot_screen = tk.Toplevel(self.root)
        self.boot_screen.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.boot_screen.configure(bg='black')
        self.boot_screen.overrideredirect(True) # Remove window decorations
        
        # "Starting Windows" text
        tk.Label(self.boot_screen, text="Starting Windows", fg='white', bg='black',
                 font=('Arial', 24, 'bold')).pack(pady=self.screen_height // 3)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.boot_screen, orient=tk.HORIZONTAL,
                                        length=400, mode='determinate')
        self.progress.pack(pady=20)
        
        # Make the boot screen modal
        self.boot_screen.grab_set()
        
        # Start the progress simulation
        self.update_progress(0)

    def update_progress(self, value):
        """Simulates the progress bar loading."""
        self.progress['value'] = value
        if value < 100:
            # Increment progress every 30ms
            self.root.after(30, self.update_progress, value + 1)
        else:
            # Boot sequence finished, destroy boot screen and load desktop
            self.boot_screen.grab_release()
            self.boot_screen.destroy()
            self.load_desktop()

    def load_desktop(self):
        """Sets up all the desktop elements after booting."""
        
        # Now that boot is done, show and maximize the main window
        self.root.deiconify()
        try:
            self.root.state('zoomed')  # Full screen like desktop
        except tk.TclError:
            # Fallback for systems that don't support 'zoomed'
            self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
            
        # Cross-platform theme
        style = ttk.Style()
        try:
            if platform.system() == 'Windows':
                style.theme_use('vista')
            else:
                style.theme_use('clam')
        except tk.TclError:
            style.theme_use('default')
        
        # Setup desktop components
        self.setup_wallpaper() # New wallpaper canvas
        self.setup_desktop_icons() # Renamed from setup_desktop
        self.setup_taskbar()
        self.show_windows_update()  # Initial update popup

    def setup_wallpaper(self):
        """Creates a blue gradient wallpaper."""
        self.wallpaper = tk.Canvas(self.root, width=self.screen_width, height=self.screen_height,
                                   highlightthickness=0)
        self.wallpaper.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create a simple vertical gradient from dark blue to lighter blue
        # This is a basic simulation of the Win7 wallpaper
        top_color = "#003087" # Darker blue
        bottom_color = "#0053AD" # Lighter blue
        
        (r1, g1, b1) = self.root.winfo_rgb(top_color)
        (r2, g2, b2) = self.root.winfo_rgb(bottom_color)
        
        for i in range(self.screen_height):
            # Calculate interpolated color
            nr = (r1 + (r2 - r1) * i // self.screen_height) >> 8
            ng = (g1 + (g2 - g1) * i // self.screen_height) >> 8
            nb = (b1 + (b2 - b1) * i // self.screen_height) >> 8
            color = f'#{nr:02x}{ng:02x}{nb:02x}'
            self.wallpaper.create_line(0, i, self.screen_width, i, fill=color)

    def setup_desktop_icons(self):
        # Desktop icons (using flat buttons for a better icon feel)
        # Using unicode characters to simulate icons
        icons = [
            ("🖥️\nDiscord", self.open_discord, 100, 100),
            ("🐍\nPython", self.open_python, 100, 200),
            ("📝\nAtom Editor", self.open_atom, 200, 100),
            ("🌐\nBrave", self.open_brave, 200, 200)
        ]
        
        # Base color for icon background (matches wallpaper)
        icon_bg = '#003087'
        
        for text, command, x, y in icons:
            icon = tk.Button(self.root, text=text, fg='white', bg=icon_bg, 
                             font=('Arial', 10, 'bold'), cursor="hand2",
                             command=command, relief='flat', borderwidth=0,
                             highlightthickness=0, compound='top', justify='center',
                             width=10, height=4, wraplength=80)
            icon.place(x=x, y=y)
    
    def setup_taskbar(self):
        # Bottom taskbar frame - Dark blue for Aero look
        taskbar_bg = "#04204A"
        taskbar = tk.Frame(self.root, bg=taskbar_bg, height=40)
        # Place taskbar above the bottom edge
        taskbar.place(x=0, y=self.screen_height-40, relwidth=1)
        
        # Start button - Styled to look more like the orb
        start_btn = tk.Button(taskbar, text="Start", bg='#1E90FF', fg='white', 
                              font=('Arial', 10, 'bold'), command=self.open_start, 
                              bd=1, relief='raised', width=6, height=1)
        start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Clock
        self.clock_label = tk.Label(taskbar, text="", bg=taskbar_bg, fg='white', font=('Arial', 10))
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self.update_clock()
    
    def update_clock(self):
        now = datetime.datetime.now().strftime("%I:%M %p") # 12-hour format
        self.clock_label.config(text=now)
        self.root.after(60000, self.update_clock)  # Update every minute
    
    def open_start(self):
        # Mock Start menu - Light blue Aero-style background
        menu = tk.Toplevel(self.root)
        menu.title("Start Menu")
        menu.geometry("300x400")
        menu.configure(bg='#EAF5FF') # Light Aero blue
        tk.Label(menu, text="All Programs\nDocuments\nSettings", 
                 bg='#EAF5FF', justify='left', anchor='w', padx=20).pack(expand=True, fill='both')
    
    def _create_basic_window(self, title, geometry):
        """Helper function to create a basic 'Aero'-styled Toplevel window."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(geometry)
        # Use a light blue background for the Aero feel
        win.configure(bg='#F0F8FF') # AliceBlue
        return win

    def open_discord(self):
        # Mock Discord chat
        win = tk.Toplevel(self.root)
        win.title("Discord")
        win.geometry("400x600")
        win.configure(bg='#36393F')  # Discord dark theme
        tk.Label(win, text="Chat Simulation\nType messages below:", bg='#36393F', fg='white').pack(pady=10)
        entry = tk.Entry(win)
        entry.pack(fill=tk.X, padx=10)
    
    def open_python(self):
        # Mock Python interpreter
        win = self._create_basic_window("Python 3.8 Interpreter", "600x400")
        text = tk.Text(win, bg='black', fg='lime green', font=('Courier', 10), insertbackground='white')
        text.pack(expand=True, fill=tk.BOTH)
        text.insert(tk.END, "Python 3.8.10 (default, Jun 22 2023, 16:00:00) \n>>> print('Hello, Win7!')\nHello, Win7!\n>>> ")
    
    def open_atom(self):
        # Mock Atom editor
        win = self._create_basic_window("Atom - program.py", "800x600")
        text = tk.Text(win, font=('Monaco', 12), wrap=tk.NONE, bg='white', fg='black')
        text.pack(expand=True, fill=tk.BOTH)
        text.insert(tk.END, "# Your code here\nimport tkinter as tk\n\nroot = tk.Tk()\nroot.mainloop()")
    
    def open_brave(self):
        # Mock Brave browser
        win = self._create_basic_window("Brave Browser", "1000x700")
        addr_frame = tk.Frame(win, bg='#EFEFEF')
        addr_frame.pack(fill=tk.X, padx=5, pady=5)
        addr = tk.Entry(addr_frame, font=('Arial', 10), bd=2, relief='sunken')
        addr.pack(fill=tk.X, ipady=4)
        addr.insert(0, "https://brave.com")
        
        web = tk.Text(win, bg='white', font=('Arial', 11))
        web.pack(expand=True, fill=tk.BOTH)
        web.insert(tk.END, "<html><body><h1>Brave Simulation</h1><p>Privacy-focused browsing on Win7.</p></body></html>")
    
    def show_windows_update(self):
        # Popup for Windows Update
        update_win = tk.Toplevel(self.root)
        update_win.title("Windows Update")
        update_win.geometry("400x300")
        update_win.configure(bg='#F0F0F0')
        update_win.transient(self.root)
        
        tk.Label(update_win, text="Important updates available.\nInstall now?", bg='#F0F0F0', font=('Arial', 12)).pack(pady=40)
        
        button_frame = tk.Frame(update_win, bg='#F0F0F0')
        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        tk.Button(button_frame, text="Install Updates", command=update_win.destroy, 
                  font=('Arial', 10, 'bold'), width=15).pack(side='right')
        tk.Button(button_frame, text="Cancel", command=update_win.destroy, width=10).pack(side='right', padx=5)


if __name__ == "__main__":
    app = Win7Simulator()
