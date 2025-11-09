import pynput.keyboard
import win32gui
import win32process
import psutil
import os
import threading
import pystray
from PIL import Image, ImageDraw
import logging # <-- NEW: For logging to a file

# --- CUSTOMIZATION ---
# 1. DEBUG MODE:
# Set to True to log debug info to "debug.log".
DEBUG_MODE = True

# 2. TOGGLE HOTKEY:
TOGGLE_MODIFIER = pynput.keyboard.Key.ctrl_l
TOGGLE_KEY = pynput.keyboard.Key.f12

# 3. FLUSH_TRIGGERS (when to save)
FLUSH_TRIGGERS = {'.', ',', '\n', '\t'}
FLUSH_BUFFER_SIZE = 50

# 4. BLOCKLIST_KEYWORDS (when to skip)
BLOCKLIST_KEYWORDS = [
    'password', 'passwort', 'email', 'e-mail',
    'login', 'log in', 'anmelden', 'anmeldung',
    'sign in', 'secure input', 'bank', 'admin',
    'keyring', 'webmail', 'invest easy', 'nippon india',
    'py - notepad++', # Python scripts in notepad++
    'new tab - google chrome'      # Chrome new tab search
]
# --- END CUSTOMIZATION ---


# --- SCRIPT SETUP ---
is_recording = True
icon = None
listener = None
current_keys = set() 
app_buffers = {}
buffer_lock = threading.Lock()
current_icon_state = 'green'
last_debugged_title = ""

# --- NEW: DEBUG LOGGER SETUP ---
DEBUG_LOG_FILE = 'debug.log'
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(message)s',
        filename=DEBUG_LOG_FILE,
        filemode='w' # 'w' = Overwrite log on each start
    )
    logging.info("Debug Logger Started.")
# --- END NEW ---

# --- ICON CREATION ---
def create_image(color_name):
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    if color_name == 'green': color = (34, 139, 34, 255)
    elif color_name == 'red': color = (178, 34, 34, 255)
    elif color_name == 'orange': color = (255, 140, 0, 255)
        
    dc.ellipse((0, 0, width - 1, height - 1), fill=color)
    return image

# --- ICON STATE MANAGER ---
def update_icon_state(new_state):
    global current_icon_state, icon
    if new_state == current_icon_state or icon is None: return
    current_icon_state = new_state
    
    if new_state == 'green': icon.icon = create_image('green')
    elif new_state == 'red': icon.icon = create_image('red')
    elif new_state == 'orange': icon.icon = create_image('orange')

# --- BUFFER & FILE FUNCTIONS ---
def flush_buffer_to_file(process_name):
    if process_name not in app_buffers or not app_buffers[process_name]: return
    log_filename = f"{process_name}.log"
    try:
        buffer_content = app_buffers[process_name]
        with open(log_filename, 'a', encoding='utf-8') as f:
            f.write(buffer_content)
        app_buffers[process_name] = ""
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Error writing to {log_filename}: {e}")

def flush_all_buffers():
    if DEBUG_MODE: logging.info("Flushing all buffers to disk...")
    with buffer_lock:
        for process_name in app_buffers.keys():
            flush_buffer_to_file(process_name)

# --- KEY LISTENER (Runs in a separate thread) ---
def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        process_name = process.name()
        return process_name.lower(), window_title
    except Exception as e:
        return None, None

def is_window_blocked(window_title):
    if not window_title:
        return True, "No Title"
    title_lower = window_title.lower()
    for keyword in BLOCKLIST_KEYWORDS:
        if keyword in title_lower:
            return True, keyword
    return False, None

# ***********************************
# *** THIS FUNCTION IS MODIFIED ***
# ***********************************
def on_press(key):
    global is_recording, current_keys, app_buffers, last_debugged_title

    # 1. CHECK HOTKEY
    if key == TOGGLE_KEY and (TOGGLE_MODIFIER in current_keys or pynput.keyboard.Key.ctrl_r in current_keys):
        toggle_recording()
        return

    # 2. ADD MODIFIERS TO SET
    if key in [pynput.keyboard.Key.ctrl_l, pynput.keyboard.Key.ctrl_r,
               pynput.keyboard.Key.alt_l, pynput.keyboard.Key.alt_r,
               pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r]:
        current_keys.add(key)

    # 3. GET WINDOW INFO
    process_name, window_title = get_active_window_info()
    if not process_name: return 

    # 4. CHECK BLOCKLIST
    is_blocked, matched_keyword = is_window_blocked(window_title)

    # 5. DEBUG MODE LOGIC (Now writes to file)
    if DEBUG_MODE and window_title != last_debugged_title:
        logging.info("---")
        logging.info(f"Title: '{window_title}'")
        logging.info(f"Process: '{process_name}'")
        
        if not is_recording: logging.info("Status: PAUSED (Icon: Red)")
        elif is_blocked: logging.info(f"Status: SKIPPING (Matched: '{matched_keyword}') (Icon: Orange)")
        else: logging.info("Status: RECORDING (Icon: Green)")
        
        last_debugged_title = window_title
    
    # 6. CHECK IF PAUSED
    if not is_recording: return

    # 7. CHECK BLOCKLIST (Action)
    if is_blocked:
        update_icon_state('orange')
        return # *** STOP HERE. DO NOT LOG. ***
    else:
        update_icon_state('green')

    # 8. PROCESS KEYSTROKE
    char_to_log = ''
    is_backspace = False
    try:
        char_to_log = key.char
    except AttributeError:
        if key == pynput.keyboard.Key.space: char_to_log = ' '
        elif key == pynput.keyboard.Key.enter: char_to_log = '\n'
        elif key == pynput.keyboard.Key.tab: char_to_log = '\t'
        elif key == pynput.keyboard.Key.backspace: is_backspace = True
        else: return
    
    # 9. UPDATE BUFFER
    should_flush = False
    with buffer_lock:
        if process_name not in app_buffers:
            app_buffers[process_name] = ""
        
        if is_backspace:
            if len(app_buffers[process_name]) > 0:
                app_buffers[process_name] = app_buffers[process_name][:-1]
        elif char_to_log:
            app_buffers[process_name] += char_to_log
            if char_to_log in FLUSH_TRIGGERS: should_flush = True
            elif len(app_buffers[process_name]) % FLUSH_BUFFER_SIZE == 0: should_flush = True
        
        if should_flush:
            flush_buffer_to_file(process_name)

def on_release(key):
    global current_keys
    try: current_keys.remove(key)
    except KeyError: pass 

def start_listener_thread():
    global listener
    listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()

# --- TRAY ICON FUNCTIONS (Run in the main thread) ---

def get_status_text(item):
    return f"Status: {current_icon_state.upper()}"

def toggle_recording():
    global is_recording
    is_recording = not is_recording
    if DEBUG_MODE: logging.info(f"Recording toggled {'ON' if is_recording else 'OFF'}")
    
    if is_recording:
        update_icon_state('green')
    else:
        flush_all_buffers()
        update_icon_state('red')
    if icon: icon.update_menu()

# --- NEW: Function to open the debug log ---
def open_debug_log(item):
    """Opens the debug.log file in the default text editor."""
    if DEBUG_MODE:
        logging.info("User requested to open debug log.")
        try:
            os.startfile(DEBUG_LOG_FILE) # This is the magic line
        except Exception as e:
            logging.error(f"Could not open debug log: {e}")
    else:
        # We can't open a log that was never created
        pass

def on_quit():
    if DEBUG_MODE: logging.info("Quit requested. Stopping...")
    flush_all_buffers()
    if listener: listener.stop()
    if icon: icon.stop()

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    listener_thread = threading.Thread(target=start_listener_thread, daemon=True)
    listener_thread.start()

    # --- NEW: Create the menu items dynamically ---
    menu_items = [
        pystray.MenuItem(get_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Toggle (Ctrl+F12)", toggle_recording),
    ]
    
    # Only add the "Open Debug Log" item if DEBUG_MODE is on
    if DEBUG_MODE:
        menu_items.append(pystray.MenuItem("Open Debug Log", open_debug_log))
    
    menu_items.extend([
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit)
    ])
    
    menu = pystray.Menu(*menu_items)
    # --- END NEW ---

    icon = pystray.Icon(
        'stateful_recorder_v9',
        icon=create_image('green'),
        title="Stateful Recorder (v9)",
        menu=menu
    )

    if DEBUG_MODE: logging.info("--- Logger Started ---")
    
    # We remove the print statements so this runs clean
    # The user should use the debug log file.
    icon.run()