import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json

def translate_key(key_str):
    """
    Returns the normalized key name.
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

def build_3column_inputs(controller_names):
    """
    Returns a dictionary with keys "buttons", "axes", "hats" containing the names
    defined in the controller profile.
    """
    result = {"buttons": [], "axes": [], "hats": []}
    if "buttons" in controller_names:
        for _, name in controller_names["buttons"].items():
            result["buttons"].append(name)
    if "axes" in controller_names:
        for _, axis in controller_names["axes"].items():
            if "positive" in axis:
                result["axes"].append(axis["positive"])
            if "negative" in axis:
                result["axes"].append(axis["negative"])
            if "trigger" in axis:
                result["axes"].append(axis["trigger"])
    if "hats" in controller_names:
        for _, hat in controller_names["hats"].items():
            for d in ["up", "down", "left", "right"]:
                if d in hat:
                    result["hats"].append(hat[d])
    return result

class MappingUI(ttk.Frame):
    """
    Displays a three-column UI for Buttons, Axes, and Hats.
    Also shows the current controller name and battery info at the top.
    """
    def __init__(self, master, categorized_inputs, mapping_dict, mapping_filename, controller_info):
        super().__init__(master, padding="10")
        self.master = master
        self.mapping_dict = mapping_dict
        self.mapping_filename = mapping_filename
        self.categorized_inputs = categorized_inputs
        self.controller_info = controller_info
        self.entries = {}
        self.create_widgets()
        self.pack(fill="both", expand=True)
    
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12))
        
        # Display controller info.
        info_label = ttk.Label(self, text=self.controller_info, font=("Helvetica", 14, "bold"))
        info_label.grid(row=0, column=0, columnspan=3, pady=(0,10))
        
        title_label = ttk.Label(self, text="Controller to Keyboard Mapper", font=("Helvetica", 16, "bold"))
        title_label.grid(row=1, column=0, columnspan=3, pady=(0,10))
        
        instruction = ttk.Label(self, text="Click a field and press a key:")
        instruction.grid(row=2, column=0, columnspan=3, pady=(0,15))
        
        # Create frames for each column.
        btn_frame = ttk.LabelFrame(self, text="Buttons", padding="10")
        axs_frame = ttk.LabelFrame(self, text="Axes", padding="10")
        hat_frame = ttk.LabelFrame(self, text="Hats", padding="10")
        btn_frame.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        axs_frame.grid(row=3, column=1, padx=5, pady=5, sticky="n")
        hat_frame.grid(row=3, column=2, padx=5, pady=5, sticky="n")
        
        row = 0
        for inp in self.categorized_inputs.get("buttons", []):
            lbl = ttk.Label(btn_frame, text=f"{inp}:")
            lbl.grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(btn_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, inp_name=inp: self.record_key(event, e, inp_name))
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row += 1
        
        row = 0
        for inp in self.categorized_inputs.get("axes", []):
            lbl = ttk.Label(axs_frame, text=f"{inp}:")
            lbl.grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(axs_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, inp_name=inp: self.record_key(event, e, inp_name))
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row += 1
        
        row = 0
        for inp in self.categorized_inputs.get("hats", []):
            lbl = ttk.Label(hat_frame, text=f"{inp}:")
            lbl.grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(hat_frame, width=15)
            if inp in self.mapping_dict:
                entry.insert(0, self.mapping_dict[inp])
            entry.bind("<FocusIn>", lambda event: self.disable_continuous())
            entry.bind("<FocusOut>", lambda event: self.enable_continuous())
            entry.bind("<Key>", lambda event, e=entry, inp_name=inp: self.record_key(event, e, inp_name))
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            self.entries[inp] = entry
            row += 1
        
        save_btn = ttk.Button(self, text="Save Mapping", command=self.save_mapping)
        save_btn.grid(row=4, column=0, columnspan=3, pady=10)
    
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

def run_ui(mapping_dict, mapping_filename, controller_name, controller_names, background_dir="ui", battery_info="N/A"):
    categorized = build_3column_inputs(controller_names)
    root = tk.Tk()
    root.title("Controller to Keyboard Mapper")
    controller_info = f"Controller: {controller_name} | Battery: {battery_info}"
    app = MappingUI(root, categorized, mapping_dict, mapping_filename, controller_info)
    root.mainloop()
