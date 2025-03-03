import pygame
import threading
import json
import time
import sys
import os
import pydirectinput  # pip install pydirectinput
from ui import run_ui

# ------------------
# CONSTANTS
# ------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

AXIS_THRESHOLD = 0.5
DEADZONE = 0.1
TRIGGER_THRESHOLD = 0.5

DATA_DIR_CONTROLLER = "controllerMappingNames"
DATA_DIR_MAPPINGS = "mappings"
DATA_DIR_UI = "ui"

REPEAT_INTERVAL = 0.05  # seconds between repeated key presses

# ------------------
# Global flag for continuous key input.
# ------------------
continuous_input_enabled = True

def load_button_names(joystick):
    js_name = joystick.get_name()
    sanitized = js_name.lower().replace(" ", "_")
    profile_filename = os.path.join(DATA_DIR_CONTROLLER, f"{sanitized}_button_names.json")
    default_filename = os.path.join(DATA_DIR_CONTROLLER, "default_button_names.json")
    
    data = None
    if os.path.exists(profile_filename):
        try:
            with open(profile_filename, "r") as f:
                data = json.load(f)
            print(f"Loaded profile from {profile_filename}")
        except Exception as e:
            print(f"Error loading {profile_filename}: {e}")
    elif os.path.exists(default_filename):
        try:
            with open(default_filename, "r") as f:
                data = json.load(f)
            print(f"Loaded default profile from {default_filename}")
        except Exception as e:
            print(f"Error loading {default_filename}: {e}")
    else:
        print("No controller profile found; using generic naming.")
    
    result = {"buttons": {}, "axes": {}, "hats": {}}
    if data:
        if "buttons" in data:
            for k, v in data["buttons"].items():
                try:
                    result["buttons"][int(k)] = v
                except:
                    pass
        if "axes" in data:
            for k, v in data["axes"].items():
                try:
                    result["axes"][int(k)] = v
                except:
                    pass
        if "hats" in data:
            for k, v in data["hats"].items():
                try:
                    result["hats"][int(k)] = v
                except:
                    pass
    return result

def get_mapping_filename(joystick):
    js_name = joystick.get_name()
    sanitized = js_name.lower().replace(" ", "_")
    if not os.path.exists(DATA_DIR_MAPPINGS):
        os.makedirs(DATA_DIR_MAPPINGS)
    return os.path.join(DATA_DIR_MAPPINGS, f"{sanitized}_mapping.json")

def controller_listener(joystick, mapping_dict, controller_names, stop_event):
    global continuous_input_enabled
    num_axes = joystick.get_numaxes()
    active_keys = {}
    last_repeat = time.time()

    while not stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                btn_name = controller_names.get("buttons", {}).get(button, f"Button {button}")
                if btn_name in mapping_dict:
                    active_keys[btn_name] = mapping_dict[btn_name]
                    print(f"[Controller] Button '{btn_name}' pressed, mapped to '{mapping_dict[btn_name]}'")
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button
                btn_name = controller_names.get("buttons", {}).get(button, f"Button {button}")
                if btn_name in active_keys:
                    print(f"[Controller] Button '{btn_name}' released")
                    active_keys.pop(btn_name, None)
            elif event.type == pygame.JOYHATMOTION:
                hat = event.hat
                x, y = event.value
                hat_names = controller_names.get("hats", {}).get(hat, {})
                up_name = hat_names.get("up", f"Hat {hat} Up")
                down_name = hat_names.get("down", f"Hat {hat} Down")
                left_name = hat_names.get("left", f"Hat {hat} Left")
                right_name = hat_names.get("right", f"Hat {hat} Right")
                if y == 1:
                    active_keys[up_name] = mapping_dict.get(up_name, None)
                    print(f"[Controller] Hat up activated, mapped to '{active_keys.get(up_name)}'")
                else:
                    active_keys.pop(up_name, None)
                if y == -1:
                    active_keys[down_name] = mapping_dict.get(down_name, None)
                    print(f"[Controller] Hat down activated, mapped to '{active_keys.get(down_name)}'")
                else:
                    active_keys.pop(down_name, None)
                if x == -1:
                    active_keys[left_name] = mapping_dict.get(left_name, None)
                    print(f"[Controller] Hat left activated, mapped to '{active_keys.get(left_name)}'")
                else:
                    active_keys.pop(left_name, None)
                if x == 1:
                    active_keys[right_name] = mapping_dict.get(right_name, None)
                    print(f"[Controller] Hat right activated, mapped to '{active_keys.get(right_name)}'")
                else:
                    active_keys.pop(right_name, None)
        
        for axis in range(num_axes):
            if axis not in controller_names.get("axes", {}):
                continue
            value = joystick.get_axis(axis)
            if abs(value) < DEADZONE:
                value = 0
            axis_def = controller_names["axes"][axis]
            if "trigger" in axis_def:
                trigger_name = axis_def["trigger"]
                if value > TRIGGER_THRESHOLD:
                    active_keys[trigger_name] = mapping_dict.get(trigger_name, None)
                    print(f"[Controller] Trigger '{trigger_name}' activated, mapped to '{mapping_dict.get(trigger_name)}'")
                else:
                    if trigger_name in active_keys:
                        print(f"[Controller] Trigger '{trigger_name}' released")
                    active_keys.pop(trigger_name, None)
            else:
                if "positive" in axis_def:
                    pos_name = axis_def["positive"]
                    if value > AXIS_THRESHOLD:
                        active_keys[pos_name] = mapping_dict.get(pos_name, None)
                        print(f"[Controller] Axis {axis} positive ('{pos_name}') activated, mapped to '{mapping_dict.get(pos_name)}'")
                    else:
                        if pos_name in active_keys:
                            print(f"[Controller] Axis {axis} positive ('{pos_name}') deactivated")
                        active_keys.pop(pos_name, None)
                if "negative" in axis_def:
                    neg_name = axis_def["negative"]
                    if value < -AXIS_THRESHOLD:
                        active_keys[neg_name] = mapping_dict.get(neg_name, None)
                        print(f"[Controller] Axis {axis} negative ('{neg_name}') activated, mapped to '{mapping_dict.get(neg_name)}'")
                    else:
                        if neg_name in active_keys:
                            print(f"[Controller] Axis {axis} negative ('{neg_name}') deactivated")
                        active_keys.pop(neg_name, None)
        
        if continuous_input_enabled:
            current_time = time.time()
            if current_time - last_repeat >= REPEAT_INTERVAL:
                for key in list(active_keys.values()):
                    if key:
                        print(f"[Controller] Repeating key: '{key}'")
                        pydirectinput.press(key)
                last_repeat = current_time
        time.sleep(0.01)

def main():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("No controller detected. Please connect a controller and try again.")
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    controller_names = load_button_names(joystick)
    mapping_filename = get_mapping_filename(joystick)

    mapping_dict = {}
    if os.path.exists(mapping_filename):
        try:
            with open(mapping_filename, "r") as f:
                mapping_dict = json.load(f)
            print(f"Loaded existing mapping from {mapping_filename}")
        except Exception as e:
            print(f"Error loading mapping from {mapping_filename}: {e}")
    else:
        print("No existing mapping found. Starting with an empty mapping.")

    try:
        battery_info = joystick.get_power_level()
    except Exception as e:
        battery_info = "N/A"
    
    stop_event = threading.Event()
    listener_thread = threading.Thread(
        target=controller_listener,
        args=(joystick, mapping_dict, controller_names, stop_event),
        daemon=True
    )
    listener_thread.start()

    controller_name = joystick.get_name()
    from ui import run_ui
    run_ui(mapping_dict, mapping_filename, controller_name, controller_names,
           background_dir=DATA_DIR_UI, battery_info=str(battery_info))

    stop_event.set()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
