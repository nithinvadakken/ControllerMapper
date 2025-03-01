import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import os
from PIL import Image, ImageTk

def translate_key(key_str):
    """
    Translates common key names into the format expected by the keyboard library.
    For example, 'left arrow' becomes 'left', etc.
    """
    key = key_str.lower().strip()
    translations = {
        "left arrow": "left",
        "arrow left": "left",
        "right arrow": "right",
        "arrow right": "right",
        "up arrow": "up",
        "arrow up": "up",
        "down arrow": "down",
        "arrow down": "down",
        "ctrl": "ctrl",
        "control": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "enter": "enter",
        "return": "enter",
        "esc": "esc",
        "escape": "esc",
        "backspace": "backspace",
        "space": "space"
    }
    return translations.get(key, key)

class MappingUIWithDiagram(ttk.Frame):
    """
    Displays a background diagram image of the controller and overlays mapping fields
    at positions loaded from a JSON file.
    """
    def __init__(self, master, input_positions, mapping_dict, mapping_filename, diagram_path, fixed_width, fixed_height):
        super().__init__(master)
        self.master = master
        self.mapping_dict = mapping_dict
        self.mapping_filename = mapping_filename
        self.diagram_path = diagram_path
        self.input_positions = input_positions  # Should be a dict mapping input names to [x, y] coordinates.
        self.fixed_width = fixed_width
        self.fixed_height = fixed_height
        self.entries = {}  # Will store input_name -> Entry widget
        self.setup_ui()
    
    def setup_ui(self):
        # Attempt to load the background diagram image.
        self.bg_image = None
        if self.diagram_path and os.path.exists(self.diagram_path):
            try:
                self.bg_image = Image.open(self.diagram_path)
                # Optionally, you can resize the image to fixed dimensions.
                self.bg_image = self.bg_image.resize((self.fixed_width, self.fixed_height))
                self.photo = ImageTk.PhotoImage(self.bg_image)
            except Exception as e:
                print(f"Error loading background image: {e}")
                self.photo = None
        else:
            print("Diagram image not found; no background will be used.")
            self.photo = None
        
        # Create a canvas with the fixed window size.
        self.canvas = tk.Canvas(self, width=self.fixed_width, height=self.fixed_height)
        self.canvas.pack(fill="both", expand=True)
        
        # If the image loaded, display it centered.
        if self.photo:
            self.canvas.create_image(self.fixed_width//2, self.fixed_height//2, anchor="center", image=self.photo)
        
        # Configure styles.
        style = ttk.Style()
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12, "bold"))
        
        # Place mapping fields with labels.
        for inp_name, coords in self.input_positions.items():
            # Ensure coordinates is a two-element list or tuple.
            if not (isinstance(coords, (list, tuple)) and len(coords) == 2):
                continue
            x, y = coords
            # Create a label (input name) to the left of the entry field.
            self.canvas.create_text(x - 40, y, text=inp_name, fill="black",
                                    anchor="e", font=("Helvetica", 12, "bold"))
            entry = ttk.Entry(self, width=10)
            if inp_name in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp_name])
            # Disable continuous key sending when editing.
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            # Pass the input name to log which input is being mapped.
            entry.bind("<Key>", lambda event, e=entry, i=inp_name: self.record_key(event, e, i))
            self.entries[inp_name] = entry
            self.canvas.create_window(x, y, window=entry)
        
        # Place a Save Mapping button at the bottom center.
        save_button = ttk.Button(self, text="Save Mapping", command=self.save_mapping)
        self.canvas.create_window(self.fixed_width // 2, self.fixed_height - 30, window=save_button)
        
        self.pack(fill="both", expand=True)
    
    def disable_continuous(self):
        import main
        main.continuous_input_enabled = False
    
    def enable_continuous(self):
        import main
        main.continuous_input_enabled = True
    
    def record_key(self, event, entry, input_name):
        key_name = event.keysym.lower()
        print(f"[UI] Mapping input '{input_name}' to key: {key_name}")
        entry.delete(0, tk.END)
        entry.insert(0, key_name)
        return "break"
    
    def save_mapping(self):
        for inp, entry in self.entries.items():
            key_input = entry.get().strip()
            if key_input:
                translated_key = translate_key(key_input)
                self.mapping_dict[inp] = translated_key
            else:
                self.mapping_dict.pop(inp, None)
        try:
            with open(self.mapping_filename, "w") as f:
                json.dump(self.mapping_dict, f, indent=4)
            messagebox.showinfo("Mapping Saved", f"Mapping saved to {self.mapping_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mapping: {e}")

class MappingUIWithoutDiagram(ttk.Frame):
    """
    Displays a fallback 3-column layout for mapping fields (Buttons, Axes, Hats)
    if no diagram/positions JSON is found.
    """
    def __init__(self, master, categorized_inputs, mapping_dict, mapping_filename):
        super().__init__(master, padding="10")
        self.master = master
        self.mapping_dict = mapping_dict
        self.mapping_filename = mapping_filename
        self.categorized_inputs = categorized_inputs  # Dictionary with keys: "buttons", "axes", "hats"
        self.entries = {}
        self.create_widgets()
        self.pack(fill="both", expand=True)
    
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12))
        
        title_label = ttk.Label(self, text="Controller to Keyboard Mapper (No Diagram Found)",
                                font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        instruction = ttk.Label(self, text="Click a field and press a key:")
        instruction.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        btn_frame = ttk.LabelFrame(self, text="Buttons", padding="10")
        axs_frame = ttk.LabelFrame(self, text="Axes", padding="10")
        hat_frame = ttk.LabelFrame(self, text="Hats", padding="10")
        
        btn_frame.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        axs_frame.grid(row=2, column=1, padx=5, pady=5, sticky="n")
        hat_frame.grid(row=2, column=2, padx=5, pady=5, sticky="n")
        
        row_btn = 0
        for inp in self.categorized_inputs.get("buttons", []):
            lbl = ttk.Label(btn_frame, text=inp + ":")
            lbl.grid(row=row_btn, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(btn_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_btn, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_btn += 1
        
        row_ax = 0
        for inp in self.categorized_inputs.get("axes", []):
            lbl = ttk.Label(axs_frame, text=inp + ":")
            lbl.grid(row=row_ax, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(axs_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_ax, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_ax += 1
        
        row_hat = 0
        for inp in self.categorized_inputs.get("hats", []):
            lbl = ttk.Label(hat_frame, text=inp + ":")
            lbl.grid(row=row_hat, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(hat_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_hat, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_hat += 1
        
        save_btn = ttk.Button(self, text="Save Mapping", command=self.save_mapping)
        save_btn.grid(row=3, column=0, columnspan=3, pady=10)
    
    def disable_continuous(self):
        import main
        main.continuous_input_enabled = False
    
    def enable_continuous(self):
        import main
        main.continuous_input_enabled = True
    
    def record_key(self, event, entry, input_name):
        key_name = event.keysym.lower()
        print(f"[UI] Mapping input '{input_name}' to key: {key_name}")
        entry.delete(0, tk.END)
        entry.insert(0, key_name)
        return "break"
    
    def save_mapping(self):
        for inp, entry in self.entries.items():
            key_input = entry.get().strip()
            if key_input:
                translated_key = translate_key(key_input)
                self.mapping_dict[inp] = translated_key
            else:
                self.mapping_dict.pop(inp, None)
        try:
            with open(self.mapping_filename, "w") as f:
                json.dump(self.mapping_dict, f, indent=4)
            messagebox.showinfo("Mapping Saved", f"Mapping saved to {self.mapping_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mapping: {e}")

def build_3column_inputs(controller_names, mapping_dict):
    """
    Builds a dictionary with keys "buttons", "axes", "hats" from the controller profile.
    """
    result = {"buttons": [], "axes": [], "hats": []}
    btn_map = controller_names.get("buttons", {})
    for idx, name in btn_map.items():
        result["buttons"].append(name)
    axs_map = controller_names.get("axes", {})
    for idx, axis_names in axs_map.items():
        pos = axis_names.get("positive", f"Axis {idx} Positive")
        neg = axis_names.get("negative", f"Axis {idx} Negative")
        result["axes"].append(pos)
        result["axes"].append(neg)
    hats_map = controller_names.get("hats", {})
    for idx, hat_dict in hats_map.items():
        up = hat_dict.get("up", f"Hat {idx} Up")
        down = hat_dict.get("down", f"Hat {idx} Down")
        left = hat_dict.get("left", f"Hat {idx} Left")
        right = hat_dict.get("right", f"Hat {idx} Right")
        result["hats"].append(up)
        result["hats"].append(down)
        result["hats"].append(left)
        result["hats"].append(right)
    return result

class MappingUIWithoutDiagram(ttk.Frame):
    """
    Displays a 3-column layout if no diagram image or positions JSON is found.
    """
    def __init__(self, master, categorized_inputs, mapping_dict, mapping_filename):
        super().__init__(master, padding="10")
        self.master = master
        self.mapping_dict = mapping_dict
        self.mapping_filename = mapping_filename
        self.categorized_inputs = categorized_inputs
        self.entries = {}
        self.create_widgets()
        self.pack(fill="both", expand=True)
    
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12))
        
        title_label = ttk.Label(self, text="Controller to Keyboard Mapper (No Diagram Found)",
                                font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        instruction = ttk.Label(self, text="Click a field and press a key:")
        instruction.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        btn_frame = ttk.LabelFrame(self, text="Buttons", padding="10")
        axs_frame = ttk.LabelFrame(self, text="Axes", padding="10")
        hat_frame = ttk.LabelFrame(self, text="Hats", padding="10")
        
        btn_frame.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        axs_frame.grid(row=2, column=1, padx=5, pady=5, sticky="n")
        hat_frame.grid(row=2, column=2, padx=5, pady=5, sticky="n")
        
        row_btn = 0
        for inp in self.categorized_inputs.get("buttons", []):
            lbl = ttk.Label(btn_frame, text=inp + ":")
            lbl.grid(row=row_btn, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(btn_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_btn, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_btn += 1
        
        row_ax = 0
        for inp in self.categorized_inputs.get("axes", []):
            lbl = ttk.Label(axs_frame, text=inp + ":")
            lbl.grid(row=row_ax, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(axs_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_ax, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_ax += 1
        
        row_hat = 0
        for inp in self.categorized_inputs.get("hats", []):
            lbl = ttk.Label(hat_frame, text=inp + ":")
            lbl.grid(row=row_hat, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(hat_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_hat, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_hat += 1
        
        save_btn = ttk.Button(self, text="Save Mapping", command=self.save_mapping)
        save_btn.grid(row=3, column=0, columnspan=3, pady=10)
    
    def disable_continuous(self):
        import main
        main.continuous_input_enabled = False
    
    def enable_continuous(self):
        import main
        main.continuous_input_enabled = True
    
    def record_key(self, event, entry, input_name):
        key_name = event.keysym.lower()
        print(f"[UI] Mapping input '{input_name}' to key: {key_name}")
        entry.delete(0, tk.END)
        entry.insert(0, key_name)
        return "break"
    
    def save_mapping(self):
        for inp, entry in self.entries.items():
            key_input = entry.get().strip()
            if key_input:
                translated_key = translate_key(key_input)
                self.mapping_dict[inp] = translated_key
            else:
                self.mapping_dict.pop(inp, None)
        try:
            with open(self.mapping_filename, "w") as f:
                json.dump(self.mapping_dict, f, indent=4)
            messagebox.showinfo("Mapping Saved", f"Mapping saved to {self.mapping_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mapping: {e}")

def build_3column_inputs(controller_names, mapping_dict):
    """
    Builds a dictionary with keys "buttons", "axes", "hats" from the controller profile.
    """
    result = {"buttons": [], "axes": [], "hats": []}
    btn_map = controller_names.get("buttons", {})
    for idx, name in btn_map.items():
        result["buttons"].append(name)
    axs_map = controller_names.get("axes", {})
    for idx, axis_names in axs_map.items():
        pos = axis_names.get("positive", f"Axis {idx} Positive")
        neg = axis_names.get("negative", f"Axis {idx} Negative")
        result["axes"].append(pos)
        result["axes"].append(neg)
    hats_map = controller_names.get("hats", {})
    for idx, hat_dict in hats_map.items():
        up = hat_dict.get("up", f"Hat {idx} Up")
        down = hat_dict.get("down", f"Hat {idx} Down")
        left = hat_dict.get("left", f"Hat {idx} Left")
        right = hat_dict.get("right", f"Hat {idx} Right")
        result["hats"].append(up)
        result["hats"].append(down)
        result["hats"].append(left)
        result["hats"].append(right)
    return result

class MappingUIWithoutDiagram(ttk.Frame):
    """
    Displays a 3-column layout (Buttons, Axes, Hats) if no diagram image or positions JSON is found.
    """
    def __init__(self, master, categorized_inputs, mapping_dict, mapping_filename):
        super().__init__(master, padding="10")
        self.master = master
        self.mapping_dict = mapping_dict
        self.mapping_filename = mapping_filename
        self.categorized_inputs = categorized_inputs
        self.entries = {}
        self.create_widgets()
        self.pack(fill="both", expand=True)
    
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12))
        
        title_label = ttk.Label(self, text="Controller to Keyboard Mapper (No Diagram Found)",
                                font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        instruction = ttk.Label(self, text="Click a field and press a key:")
        instruction.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        btn_frame = ttk.LabelFrame(self, text="Buttons", padding="10")
        axs_frame = ttk.LabelFrame(self, text="Axes", padding="10")
        hat_frame = ttk.LabelFrame(self, text="Hats", padding="10")
        
        btn_frame.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        axs_frame.grid(row=2, column=1, padx=5, pady=5, sticky="n")
        hat_frame.grid(row=2, column=2, padx=5, pady=5, sticky="n")
        
        row_btn = 0
        for inp in self.categorized_inputs.get("buttons", []):
            lbl = ttk.Label(btn_frame, text=inp + ":")
            lbl.grid(row=row_btn, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(btn_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_btn, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_btn += 1
        
        row_ax = 0
        for inp in self.categorized_inputs.get("axes", []):
            lbl = ttk.Label(axs_frame, text=inp + ":")
            lbl.grid(row=row_ax, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(axs_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_ax, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_ax += 1
        
        row_hat = 0
        for inp in self.categorized_inputs.get("hats", []):
            lbl = ttk.Label(hat_frame, text=inp + ":")
            lbl.grid(row=row_hat, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(hat_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, i=inp: self.record_key(event, e, i))
            entry.grid(row=row_hat, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row_hat += 1
        
        save_btn = ttk.Button(self, text="Save Mapping", command=self.save_mapping)
        save_btn.grid(row=3, column=0, columnspan=3, pady=10)
    
    def disable_continuous(self):
        import main
        main.continuous_input_enabled = False
    
    def enable_continuous(self):
        import main
        main.continuous_input_enabled = True
    
    def record_key(self, event, entry, input_name):
        key_name = event.keysym.lower()
        print(f"[UI] Mapping input '{input_name}' to key: {key_name}")
        entry.delete(0, tk.END)
        entry.insert(0, key_name)
        return "break"
    
    def save_mapping(self):
        for inp, entry in self.entries.items():
            key_input = entry.get().strip()
            if key_input:
                translated_key = translate_key(key_input)
                self.mapping_dict[inp] = translated_key
            else:
                self.mapping_dict.pop(inp, None)
        try:
            with open(self.mapping_filename, "w") as f:
                json.dump(self.mapping_dict, f, indent=4)
            messagebox.showinfo("Mapping Saved", f"Mapping saved to {self.mapping_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mapping: {e}")

def build_3column_inputs(controller_names, mapping_dict):
    """
    Builds a dictionary with keys "buttons", "axes", "hats" from the controller profile.
    """
    result = {"buttons": [], "axes": [], "hats": []}
    btn_map = controller_names.get("buttons", {})
    for idx, name in btn_map.items():
        result["buttons"].append(name)
    axs_map = controller_names.get("axes", {})
    for idx, axis_names in axs_map.items():
        pos = axis_names.get("positive", f"Axis {idx} Positive")
        neg = axis_names.get("negative", f"Axis {idx} Negative")
        result["axes"].append(pos)
        result["axes"].append(neg)
    hats_map = controller_names.get("hats", {})
    for idx, hat_dict in hats_map.items():
        up = hat_dict.get("up", f"Hat {idx} Up")
        down = hat_dict.get("down", f"Hat {idx} Down")
        left = hat_dict.get("left", f"Hat {idx} Left")
        right = hat_dict.get("right", f"Hat {idx} Right")
        result["hats"].append(up)
        result["hats"].append(down)
        result["hats"].append(left)
        result["hats"].append(right)
    return result

def run_ui(mapping_dict, mapping_filename, controller_name, controller_names, background_dir="ui", fixed_width=1200, fixed_height=700):
    """
    Checks if a diagram image ([sanitized].png) and a positions JSON ([sanitized]_positions.json)
    exist in background_dir.
      - If found, loads them and uses MappingUIWithDiagram (with fixed window size).
      - Otherwise, builds a 3-column layout using MappingUIWithoutDiagram.
    """
    sanitized = controller_name.lower().replace(" ", "_")
    diagram_path = os.path.join(background_dir, f"{sanitized}/{sanitized}.png")
    positions_path = os.path.join(background_dir, f"{sanitized}/{sanitized}_positions.json")
    
    root = tk.Tk()
    root.title("Controller to Keyboard Mapper")
    # Set fixed window size.
    root.geometry(f"{fixed_width}x{fixed_height}")
    
    if os.path.exists(diagram_path) and os.path.exists(positions_path):
        try:
            with open(positions_path, "r") as f:
                input_positions = json.load(f)
            app = MappingUIWithDiagram(root, input_positions, mapping_dict, mapping_filename, diagram_path, fixed_width, fixed_height)
        except Exception as e:
            messagebox.showwarning("Positions Error", f"Failed to parse positions JSON: {e}\nFalling back to 3-column layout.")
            categorized = build_3column_inputs(controller_names, mapping_dict)
            app = MappingUIWithoutDiagram(root, categorized, mapping_dict, mapping_filename)
    else:
        categorized = build_3column_inputs(controller_names, mapping_dict)
        app = MappingUIWithoutDiagram(root, categorized, mapping_dict, mapping_filename)
    
    root.mainloop()
