import pynput.keyboard
import win32gui
import win32process
import psutil
import os
import threading
import pystray
from PIL import Image, ImageDraw
import logging # For logging to a file

# --- CUSTOMIZATION ---
DEBUG_MODE = True
TOGGLE_MODIFIER = pynput.keyboard.Key.ctrl_l
TOGGLE_KEY = pynput.keyboard.Key.f12
# --- END CUSTOMIZATION ---


# --- SCRIPT SETUP ---
is_recording = True
icon = None
listener = None
current_keys = set() 
current_icon_state = 'green'
last_debugged_title = ""
current_window_title = ""
current_process_name = "" 
dynamic_blocklist = set()
# Tracks the last app we logged to for smart newlines
last_logged_process = None 

# --- DEBUG LOGGER SETUP ---
DEBUG_LOG_FILE = 'debug.log'
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(message)s',
        filename=DEBUG_LOG_FILE,
        filemode='w'
    )
    logging.info("Debug Logger Started.")

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

# --- NEW: RAW LOGGING FUNCTION ---
def log_event(process_name, event_text):
    """
    Appends the raw event text to the correct log file with smart newlines
    for app-switching.
    """
    global last_logged_process
    try:
        log_filename = f"{process_name}.log"
        prefix = ""
        
        # If we are logging to a new app, add a newline first
        if process_name != last_logged_process:
            if event_text != "\n": # Don't add a double newline
                prefix = "\n"
            last_logged_process = process_name
            
        with open(log_filename, 'a', encoding='utf-8') as f:
            f.write(prefix + event_text)
            
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Error writing to {log_filename}: {e}")

# --- BLOCKLIST FUNCTIONS ---
def load_dynamic_blocklist():
    """Loads all lines from my_blocklist.txt into one set."""
    global dynamic_blocklist
    
    dynamic_blocklist.clear()
    
    try:
        if not os.path.exists(BLOCKLIST_FILE):
            if DEBUG_MODE: logging.info(f"'{BLOCKLIST_FILE}' not found, creating with defaults.")
            default_rules = [
                '# This is your blocklist. Lines starting with # are comments.',
                '# Any window title *containing* a line from this file will be blocked.',
                '# Add single words (like "password") or full titles.',
                'password',
                'passwort',
                'login',
                'log in',
                'anmelden',
                'sign in',
                'email',
                'e-mail',
                'secure input',
                'bank',
                'admin',
                'keyring'
            ]
            with open(BLOCKLIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(default_rules))

        with open(BLOCKLIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower() # Read all as lowercase
                if not line or line.startswith('#'):
                    continue
                dynamic_blocklist.add(line)
        
        if DEBUG_MODE:
            logging.info(f"Loaded {len(dynamic_blocklist)} blocklist keywords.")
            
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Failed to load dynamic blocklist: {e}")

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
    """Checks if the title contains any line from the blocklist."""
    global dynamic_blocklist
    
    if not window_title:
        return True, "No Title"
        
    title_lower = window_title.lower()

    for keyword in dynamic_blocklist:
        if keyword in title_lower:
            return True, f"Keyword: '{keyword}'"
            
    return False, None

# ***********************************
# *** THIS FUNCTION IS MODIFIED ***
# ***********************************
def on_press(key):
    global is_recording, current_keys, last_debugged_title
    global current_window_title, current_process_name

    # 1. CHECK HOTKEY (Ctrl+F12)
    # We check if F12 is pressed *while* Ctrl is already held.
    if key == TOGGLE_KEY and (TOGGLE_MODIFIER in current_keys or pynput.keyboard.Key.ctrl_r in current_keys):
        toggle_recording()
        return # Don't log the hotkey

    # 2. ADD MODIFIERS TO SET
    if key in [pynput.keyboard.Key.ctrl_l, pynput.keyboard.Key.ctrl_r,
               pynput.keyboard.Key.alt_l, pynput.keyboard.Key.alt_r,
               pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r,
               pynput.keyboard.Key.cmd, pynput.keyboard.Key.cmd_r]:
        current_keys.add(key)
        # We also log modifiers below

    # 3. GET WINDOW INFO
    process_name, window_title = get_active_window_info()
    if not process_name: return 
    
    current_window_title = window_title
    current_process_name = process_name

    # 4. CHECK BLOCKLIST
    is_blocked, matched_keyword = is_window_blocked(window_title)

    # 5. DEBUG MODE LOGIC
    if DEBUG_MODE and window_title != last_debugged_title:
        logging.info("---")
        logging.info(f"Title: '{window_title}'")
        logging.info(f"Process: '{process_name}'")
        if not is_recording: logging.info("Status: PAUSED (Icon: Red)")
        elif is_blocked: logging.info(f"Status: SKIPPING (Matched: {matched_keyword}) (Icon: Orange)")
        else: logging.info("Status: RECORDING (Icon: Green)")
        last_debugged_title = window_title
    
    # 6. CHECK IF PAUSED
    if not is_recording:
        update_icon_state('red')
        return

    # 7. CHECK BLOCKLIST (Action)
    if is_blocked:
        update_icon_state('orange')
        return
    else:
        update_icon_state('green')

    # 8. PROCESS KEYSTROKE (NEW RAW LOGIC)
    log_entry = ''
    try:
        # This is a normal character (e.g., 'h', 'a', '1')
        log_entry = key.char
        if log_entry is None: # This happens on Ctrl+A
             log_entry = f"[{key.name}]"
    except AttributeError:
        # This is a special key
        if key == pynput.keyboard.Key.enter:
            log_entry = "\n"
        elif key == pynput.keyboard.Key.space:
            log_entry = " "
        elif key == pynput.keyboard.Key.tab:
            log_entry = "\t"
        else:
            # This logs [backspace], [delete], [ctrl_l], [a], etc.
            log_entry = f"[{key.name}]"
    
    # 9. LOG THE EVENT
    log_event(process_name, log_entry)
# ***********************************
# *** END OF MODIFIED FUNCTION ***
# ***********************************

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
    
    # We just update the icon state. No buffers to flush.
    if is_recording:
        update_icon_state('green')
    else:
        update_icon_state('red')
    if icon: icon.update_menu()

def open_debug_log(item):
    if DEBUG_MODE:
        logging.info("User requested to open debug log.")
        try: os.startfile(DEBUG_LOG_FILE)
        except Exception as e: logging.error(f"Could not open debug log: {e}")

def block_current_window(item):
    """Adds the current window's exact title to the blocklist file."""
    global current_window_title, current_process_name, dynamic_blocklist
    
    title_to_block = current_window_title
    
    if not title_to_block:
        if DEBUG_MODE: logging.warning("Block request: No title found.")
        return
        
    if title_to_block.lower() in dynamic_blocklist:
        if DEBUG_MODE: logging.info(f"Block request: '{title_to_block}' is already in the list.")
        return
        
    try:
        with open(BLOCKLIST_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{title_to_block}")
        
        dynamic_blocklist.add(title_to_block.lower())
        
        # No buffer to clear!
        
        if DEBUG_MODE: logging.info(f"Dynamically blocked: '{title_to_block}'")
        
        update_icon_state('orange') 
        if icon: icon.update_menu()
        
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Failed to add to blocklist: {e}")

def open_blocklist_file(item):
    """Opens my_blocklist.txt in the default text editor."""
    try:
        os.startfile(BLOCKLIST_FILE)
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Could not open blocklist file: {e}")

def reload_blocklist(item):
    """Reloads the blocklist file from disk."""
    if DEBUG_MODE: logging.info("User requested blocklist reload.")
    load_dynamic_blocklist()
    global last_debugged_title
    last_debugged_title = "" 
    if icon: icon.update_menu()

def open_script_folder(item):
    """Opens the script's current directory in Windows Explorer."""
    try:
        # __file__ is the path to the current script
        script_dir = os.path.abspath(os.path.dirname(__file__))
        os.startfile(script_dir)
        if DEBUG_MODE: logging.info(f"Opening script folder: {script_dir}")
    except Exception as e:
        if DEBUG_MODE: logging.error(f"Could not open script folder: {e}")

def on_quit():
    if DEBUG_MODE: logging.info("Quit requested. Stopping...")
    # No buffers to flush
    if listener: listener.stop()
    if icon: icon.stop()
    if DEBUG_MODE: logging.info("--- Logger Stopped ---")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    load_dynamic_blocklist()

    listener_thread = threading.Thread(target=start_listener_thread, daemon=True)
    listener_thread.start()

    menu_items = [
        pystray.MenuItem(get_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Toggle (Ctrl+F12)", toggle_recording),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Block Current Window", block_current_window),
        pystray.MenuItem("Open Blocklist File", open_blocklist_file),
        pystray.MenuItem("Reload Blocklist", reload_blocklist),
        pystray.MenuItem("Open Log/Script Folder", open_script_folder), # Added
    ]
    if DEBUG_MODE:
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Debug Log", open_debug_log)
        ])
    menu_items.extend([
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit)
    ])
    menu = pystray.Menu(*menu_items)

    icon = pystray.Icon(
        'raw_keyboard_recorder_v27',
        icon=create_image('green'),
        title="Raw Keyboard Recorder (v27)",
        menu=menu
    )

    if DEBUG_MODE: logging.info("--- Logger Started ---")
    
    icon.run()
