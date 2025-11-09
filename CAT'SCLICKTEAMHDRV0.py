import tkinter as tk
from tkinter import ttk
from tkinter import font

class ClickteamEditorMock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cat's Clickteam 0.1")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.configure(bg='#e0e0e0')  # XP-era gray-blue wash
        
        # Menu bar: exact cascade from PNG
        self.menubar = tk.Menu(self.root, bg='lightblue', fg='black', font=('Arial', 9))
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0, bg='lightblue')
        file_menu.add_command(label="New", accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", accelerator="Ctrl+O")
        file_menu.add_command(label="Save", accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit")
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit
        edit_menu = tk.Menu(self.menubar, tearoff=0, bg='lightblue')
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V")
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View
        view_menu = tk.Menu(self.menubar, tearoff=0, bg='lightblue')
        view_menu.add_command(label="Zoom In")
        view_menu.add_command(label="Zoom Out")
        self.menubar.add_cascade(label="View", menu=view_menu)
        
        # Insert
        insert_menu = tk.Menu(self.menubar, tearoff=0, bg='lightblue')
        insert_menu.add_command(label="Object")
        insert_menu.add_command(label="Counter")
        self.menubar.add_cascade(label="Insert", menu=insert_menu)
        
        # Layout / Frame / Objects / Conditions / Expressions / Tools / Options / Window / Help
        for menu_name in ['Layout', 'Frame', 'Objects', 'Conditions', 'Expressions', 'Tools', 'Options', 'Window', 'Help']:
            dummy_menu = tk.Menu(self.menubar, tearoff=0, bg='lightblue')
            dummy_menu.add_command(label=f"{menu_name} Placeholder")
            self.menubar.add_cascade(label=menu_name, menu=dummy_menu)
        
        # Toolbar: proxy icons as labeled buttons, row of relics
        toolbar_frame = tk.Frame(self.root, bg='lightgray', height=30, relief=tk.RAISED, bd=1)
        toolbar_frame.pack(fill=tk.X, padx=2, pady=2)
        toolbar_frame.pack_propagate(False)
        
        toolbar_items = [
            ('New', 'Ctrl+N'), ('Open', 'Ctrl+O'), ('Save', 'Ctrl+S'),
            ('|'),  # Separator
            ('Undo', 'Ctrl+Z'), ('Redo', 'Ctrl+Y'),
            ('|'),
            ('Cut', 'Ctrl+X'), ('Copy', 'Ctrl+C'), ('Paste', 'Ctrl+V'),
            ('|'),
            ('Select', 'S'), ('Brush', 'B'), ('Fill', 'F'), ('Line', 'L'),
            ('|'),
            ('Zoom In', '+'), ('Zoom Out', '-'), ('Hand', 'H'),
            ('|'),
            ('Properties', 'P'), ('Events', 'E'), ('Gear', 'Settings')
        ]
        
        for item in toolbar_items:
            if item == '|':
                sep = tk.Frame(toolbar_frame, width=2, bg='gray', height=20)
                sep.pack(side=tk.LEFT, padx=2)
            else:
                btn = tk.Button(toolbar_frame, text=item[0], width=8, bg='lightblue', fg='black', font=('Arial', 8),
                                relief=tk.RAISED, bd=1, command=lambda x=item[0]: self.dummy_action(x))
                btn.pack(side=tk.LEFT, padx=1)
        
        # Main container: split into left (objects), center (frame), right (properties)
        main_frame = tk.Frame(self.root, bg='#e0e0e0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Left panel: Objects list
        left_frame = tk.Frame(main_frame, width=150, bg='white', relief=tk.SUNKEN, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        left_frame.pack_propagate(False)
        
        objects_label = tk.Label(left_frame, text="Objects", bg='lightblue', fg='black', font=('Arial', 10, 'bold'),
                                 relief=tk.RAISED, bd=1, anchor='w')
        objects_label.pack(fill=tk.X)
        
        # Treeview for object hierarchy, mimicking PNG list
        self.objects_tree = ttk.Treeview(left_frame, height=20, columns=('Type',), show='tree headings')
        self.objects_tree.heading('#0', text='Icon/Name')
        self.objects_tree.heading('#1', text='Type')
        self.objects_tree.column('#0', width=80)
        self.objects_tree.column('#1', width=60)
        
        # Sample items from PNG
        sample_objects = [
            ('Active', 'Counter'), ('Active', 'Circle'), ('Active', 'Cube'),
            ('Text', 'Label'), ('Active', 'Button'), ('Text', 'Input'),
            ('Active', 'Grid'), ('Background', 'Layer')
        ]
        for obj in sample_objects:
            iid = self.objects_tree.insert('', 'end', text=obj[0], values=(obj[1],))
        
        scrollbar_left = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.objects_tree.yview)
        self.objects_tree.configure(yscrollcommand=scrollbar_left.set)
        self.objects_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Center: Main frame editor - empty canvas, white void with faint grid echo
        center_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        self.frame_canvas = tk.Canvas(center_frame, width=400, height=500, bg='white', highlightthickness=1, highlightbackground='black')
        self.frame_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Faint selection border/handles, dormant
        self.frame_canvas.create_rectangle(10, 10, 390, 490, outline='blue', width=1, dash=(5, 5))
        # Subtle grid
        for i in range(0, 401, 20):
            self.frame_canvas.create_line(0, i, 400, i, fill='lightgray', width=1)
            self.frame_canvas.create_line(i, 0, i, 400, fill='lightgray', width=1)
        
        # Right panel: Properties
        right_frame = tk.Frame(main_frame, width=200, bg='white', relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        right_frame.pack_propagate(False)
        
        props_label = tk.Label(right_frame, text="Properties", bg='lightblue', fg='black', font=('Arial', 10, 'bold'),
                               relief=tk.RAISED, bd=1, anchor='w')
        props_label.pack(fill=tk.X)
        
        # Notebook for tabs: General, Size & Position, Events
        self.props_notebook = ttk.Notebook(right_frame)
        self.props_notebook.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # General tab: empty
        general_tab = tk.Frame(self.props_notebook, bg='white')
        tk.Label(general_tab, text="General Properties\n(Empty for new frame)", bg='white', fg='gray').pack(expand=True)
        self.props_notebook.add(general_tab, text='General')
        
        # Size & Position tab: placeholders
        size_tab = tk.Frame(self.props_notebook, bg='white')
        tk.Label(size_tab, text="Width: 400\nHeight: 300\nX: 0\nY: 0", justify=tk.LEFT, bg='white', fg='black').pack(anchor='w', padx=10, pady=10)
        self.props_notebook.add(size_tab, text='Size & Position')
        
        # Events tab: with controls echoing PNG (Date, Style, Styles? - interpreted as samples)
        events_tab = tk.Frame(self.props_notebook, bg='white')
        tk.Label(events_tab, text="Events", font=('Arial', 9, 'bold'), bg='white').pack(anchor='w', padx=10)
        tk.Label(events_tab, text="Date:", bg='white').pack(anchor='w', padx=10)
        date_spin = tk.Spinbox(events_tab, from_=1900, to=2100, width=10)
        date_spin.pack(anchor='w', padx=20, pady=2)
        tk.Label(events_tab, text="Style:", bg='white').pack(anchor='w', padx=10)
        style_combo = ttk.Combobox(events_tab, values=['Default', 'Bold', 'Italic'], width=15, state='readonly')
        style_combo.pack(anchor='w', padx=20, pady=2)
        tk.Label(events_tab, text="Styles:", bg='white').pack(anchor='w', padx=10)
        styles_list = tk.Listbox(events_tab, height=4, width=20)
        styles_list.pack(anchor='w', padx=20, pady=2)
        self.props_notebook.add(events_tab, text='Events')
        
        # Status bar: bottom whisper
        status_frame = tk.Frame(self.root, bg='lightgray', height=20, relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        self.status_label = tk.Label(status_frame, text="Ready", bg='lightgray', fg='black', anchor='w', font=('Arial', 8))
        self.status_label.pack(side=tk.LEFT, padx=5)
        tk.Label(status_frame, text="100%", bg='lightgray', anchor='e').pack(side=tk.RIGHT, padx=5)  # Zoom proxy
    
    def dummy_action(self, action):
        self.status_label.config(text=f"{action} invoked - mock response")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    editor = ClickteamEditorMock()
    editor.run()
