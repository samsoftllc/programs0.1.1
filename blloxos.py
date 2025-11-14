import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, messagebox
import io
import contextlib
import sys

# -----------------------------
# Fake Roblox Mini-Game:
# STEAL A CAT: ROT PLAYABLE
# -----------------------------
def open_steal_a_cat_game():
    game = tk.Toplevel()
    game.title("STEAL A CAT: ROT PLAYABLE")
    game.geometry("500x400")
    game.resizable(False, False)
    game.config(bg="#222222")

    canvas = tk.Canvas(game, width=480, height=300, bg="#333333", highlightthickness=0)
    canvas.pack(pady=10)

    # Cat (blue square)
    cat = canvas.create_rectangle(50, 150, 90, 190, fill="#66aaff")

    # Thief (red circle)
    thief = canvas.create_oval(300, 150, 340, 190, fill="#ff4444")

    speed = 4
    thief_speed = 2

    def move_cat(dx, dy):
        canvas.move(cat, dx, dy)

    def game_loop():
        # Need to check if canvas exists before trying to get coords
        if not canvas.winfo_exists():
            return
            
        try:
            cx1, cy1, cx2, cy2 = canvas.coords(cat)
            tx1, ty1, tx2, ty2 = canvas.coords(thief)

            # Thief moves toward cat
            if tx1 < cx1: canvas.move(thief, thief_speed, 0)
            if tx1 > cx1: canvas.move(thief, -thief_speed, 0)
            if ty1 < cy1: canvas.move(thief, 0, thief_speed)
            if ty1 > cy1: canvas.move(thief, 0, -thief_speed)

            # Collision?
            if abs(cx1 - tx1) < 25 and abs(cy1 - ty1) < 25:
                # Check if game window still exists before showing messagebox
                if game.winfo_exists():
                    tk.messagebox.showinfo("OH NO!", "😹 YOU GOT STEALED!\nThe thief stole the cat!")
                    reset()
                return # Stop loop on collision

            game.after(30, game_loop)
        except tk.TclError:
            # This can happen if the window is closed while the loop is running
            pass

    def reset():
        if canvas.winfo_exists():
            canvas.coords(cat, 50, 150, 90, 190)
            canvas.coords(thief, 300, 150, 340, 190)

    game.bind("<Up>", lambda e: move_cat(0, -speed))
    game.bind("<Down>", lambda e: move_cat(0, speed))
    game.bind("<Left>", lambda e: move_cat(-speed, 0))
    game.bind("<Right>", lambda e: move_cat(speed, 0))

    ttk.Button(game, text="Reset", command=reset).pack()

    game_loop()



# -----------------------------
# Fake Roblox Window w/ Guest
# -----------------------------
def open_fake_roblox():
    roblox = tk.Toplevel()
    roblox.title("ROBLOX")
    roblox.geometry("420x450")
    roblox.config(bg="#1b1b1b")

    title = tk.Label(
        roblox,
        text="ROBLOX",
        font=("Arial Black", 22),
        fg="#ff4444",
        bg="#1b1b1b"
    )
    title.pack(pady=10)

    guest = tk.Label(
        roblox,
        text="Logged in as: GUEST",
        font=("Arial", 12),
        fg="#cccccc",
        bg="#1b1b1b"
    )
    guest.pack(pady=5)

    # Game Tiles Section
    games_label = tk.Label(
        roblox,
        text="Games",
        font=("Arial", 14),
        fg="#ffffff",
        bg="#1b1b1b"
    )
    games_label.pack(pady=5)

    # --- Game Tile: STEAL A CAT ---
    frame = tk.Frame(roblox, bg="#222222", width=360, height=80)
    frame.pack(pady=10, padx=10)
    frame.pack_propagate(False)

    tk.Label(
        frame,
        text="STEAL A CAT: ROT PLAYABLE",
        fg="#ffffff",
        bg="#222222",
        font=("Arial", 12, "bold")
    ).pack(pady=5)

    ttk.Button(frame, text="Play", command=open_steal_a_cat_game).pack()

    # Extra buttons
    ttk.Button(roblox, text="Avatar", width=20).pack(pady=5)
    ttk.Button(roblox, text="Games", width=20).pack(pady=5)
    ttk.Button(roblox, text="Leave", width=20, command=roblox.destroy).pack(pady=10)


# --- Main Application Class ---
class CatNtApp:
    def __init__(self, root):
        self.root = root
        self.root.title("cat nt")
        self.root.geometry("600x400")
        
        # --- Apply a Theme ---
        # We use ttk (themed tkinter) for a more modern look.
        # We'll try to use a Windows-native theme if available.
        self.style = ttk.Style()
        try:
            # 'vista' or 'xpnative' often look best on Windows
            if sys.platform == "win32":
                self.style.theme_use('vista')
            else:
                # Use the default theme on other OSes
                self.style.theme_use('default')
        except tk.TclError:
            # Fallback if the theme doesn't exist
            self.style.theme_use('default')

        # --- Configure Grid Layout ---
        # We'll make the main PanedWindow fill the entire root window,
        # and the button will sit at the bottom.
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Create Paned Window ---
        # This creates a resizable divider between the code and output areas.
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # --- Code Input Frame ---
        self.code_frame = ttk.Frame(self.paned_window, padding=5)
        self.code_frame.grid_rowconfigure(1, weight=1)
        self.code_frame.grid_columnconfigure(0, weight=1)
        
        self.code_label = ttk.Label(self.code_frame, text="Python Interpreter:")
        self.code_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Using scrolledtext for automatic scrollbars
        self.code_input = scrolledtext.Text(self.code_frame, wrap=tk.WORD, height=10, bg="#2d2d2d", fg="#cccccc", insertbackground="#ffffff", font=("Consolas", 10))
        self.code_input.grid(row=1, column=0, sticky="nsew")
        
        self.paned_window.add(self.code_frame, weight=3) # Give more space to code input

        # --- Output Frame ---
        self.output_frame = ttk.Frame(self.paned_window, padding=5)
        self.output_frame.grid_rowconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_label = ttk.Label(self.output_frame, text="Output:")
        self.output_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.output_display = scrolledtext.Text(self.output_frame, wrap=tk.WORD, height=5, state=tk.DISABLED, bg="#1e1e1e", fg="#888888", font=("Consolas", 10))
        self.output_display.grid(row=1, column=0, sticky="nsew")

        self.paned_window.add(self.output_frame, weight=1) # Give less space to output

        # --- Button Frame ---
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        # --- Run Button ---
        self.run_button = ttk.Button(self.bottom_frame, text="Run Code", command=self.execute_code)
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # --- Roblox Button ---
        self.roblox_button = ttk.Button(self.bottom_frame, text="Open Fake Roblox", command=open_fake_roblox)
        self.roblox_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def execute_code(self):
        """
        Executes the code from the input box and displays the output.
        
        SECURITY WARNING:
        Using exec() on user-supplied input is EXTREMELY DANGEROUS.
        This code will run ANY Python command, including deleting files
        (e.g., 'import os; os.remove("some_file")').
        This should NEVER be used in a real-world application
        without extreme sandboxing.
        """
        
        # Get the code from the input widget
        code = self.code_input.get("1.0", tk.END)
        
        # Create in-memory "files" to capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Clear the output display
        self.output_display.config(state=tk.NORMAL)
        self.output_display.delete("1.0", tk.END)
        self.output_display.config(fg="#cccccc") # Reset to default text color
        
        try:
            # Redirect stdout and stderr
            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    # Execute the code
                    # We use a local_vars dict to capture any variables created
                    local_vars = {}
                    exec(code, globals(), local_vars)
            
            # Get the captured output
            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()
            
            if stdout_val:
                self.output_display.insert(tk.END, stdout_val)
                
            if stderr_val:
                # Show errors in a different color
                self.output_display.config(fg="#ff8888") # Light red for errors
                self.output_display.insert(tk.END, stderr_val)
                
            if not stdout_val and not stderr_val:
                self.output_display.config(fg="#888888") # Grey for no output
                self.output_display.insert(tk.END, "Code executed with no output.")

        except Exception as e:
            # Catch syntax errors or other exceptions
            self.output_display.config(fg="#ff8888") # Light red for errors
            self.output_display.insert(tk.END, f"An error occurred:\n{e}")
            
        finally:
            # Make the output box read-only again
            self.output_display.config(state=tk.DISABLED)
            # Clean up the string buffers
            stdout_capture.close()
            stderr_capture.close()

# --- Run the Application ---
if __name__ == "__main__":
    # Create the main window
    main_root = tk.Tk()
    
    # Create an instance of the app
    app = CatNtApp(main_root)
    
    # Start the Tkinter event loop
    main_root.mainloop()
