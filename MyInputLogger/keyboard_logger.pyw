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
FLUSH_TRIGGERS = {'.', ',', '\n', '\t'}
FLUSH_BUFFER_SIZE = 50

# The one and only blocklist file
BLOCKLIST_FILE = 'my_blocklist.txt'
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
current_window_title = ""
current_process_name = "" 

# NEW: We only have one list now
dynamic_blocklist = set()

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

# --- BLOCKLIST FUNCTIONS (MODIFIED) ---
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

# --- IS_WINDOW_BLOCKED (MODIFIED) ---
def is_window_blocked(window_title):
    """Checks if the title contains any line from the blocklist."""
    global dynamic_blocklist
    
    if not window_title:
        return True, "No Title"
        
    title_lower = window_title.lower()

    # The one, simple check:
    for keyword in dynamic_blocklist:
        if keyword in title_lower:
            return True, f"Keyword: '{keyword}'"
            
    return False, None

def on_press(key):
    global is_recording, current_keys, app_buffers, last_debugged_title
    global current_window_title, current_process_name

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
    if not is_recording: return

    # 7. CHECK BLOCKLIST (Action)
    if is_blocked:
        update_icon_state('orange')
        return
    else:
        update_icon_state('green')

    # 8. PROCESS KEYSTROKE
    char_to_log = ''
    is_backspace = False
    try: char_to_log = key.char
    except AttributeError:
        if key == pynput.keyboard.Key.space: char_to_log = ' '
        elif key == pynput.keyboard.Key.enter: char_to_log = '\n'
        elif key == pynput.keyboard.Key.tab: char_to_log = '\t'
        elif key == pynput.keyboard.Key.backspace: is_backspace = True
        else: return
    
    # 9. UPDATE BUFFER
    should_flush = False
    with buffer_lock:
        if process_name not in app_buffers: app_buffers[process_name] = ""
        if is_backspace:
            if len(app_buffers[process_name]) > 0:
                app_buffers[process_name] = app_buffers[process_name][:-1]
        elif char_to_log:
            app_buffers[process_name] += char_to_log
            if char_to_log in FLUSH_TRIGGERS: should_flush = True
            elif len(app_buffers[process_name]) % FLUSH_BUFFER_SIZE == 0: should_flush = True
        if should_flush: flush_buffer_to_file(process_name)

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
    if is_recording: update_icon_state('green')
    else:
        flush_all_buffers()
        update_icon_state('red')
    if icon: icon.update_menu()

def open_debug_log(item):
    if DEBUG_MODE:
        logging.info("User requested to open debug log.")
        try: os.startfile(DEBUG_LOG_FILE)
        except Exception as e: logging.error(f"Could not open debug log: {e}")

# --- BLOCKLIST MENU FUNCTIONS (MODIFIED) ---
def block_current_window(item):
    """Adds the current window's exact title to the blocklist file."""
    global current_window_title, current_process_name, dynamic_blocklist, app_buffers, buffer_lock
    
    title_to_block = current_window_title
    proc_to_clear = current_process_name
    
    if not title_to_block:
        if DEBUG_MODE: logging.warning("Block request: No title found.")
        return
        
    # Check the in-memory list (we must lowercase the title to check)
    if title_to_block.lower() in dynamic_blocklist:
        if DEBUG_MODE: logging.info(f"Block request: '{title_to_block}' is already in the list.")
        return
        
    try:
        # Add the exact title to the file (it will be lowercased on next load)
        with open(BLOCKLIST_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{title_to_block}")
        
        # Add the lowercased version to the in-memory set
        dynamic_blocklist.add(title_to_block.lower())
        
        with buffer_lock:
            if proc_to_clear and proc_to_clear in app_buffers:
                del app_buffers[proc_to_clear]
                if DEBUG_MODE: logging.info(f"Cleared sensitive buffer for '{proc_to_clear}'")
        
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
    # Force an update on the current window
    global last_debugged_title
    last_debugged_title = "" 
    if icon: icon.update_menu()

def on_quit():
    if DEBUG_MODE: logging.info("Quit requested. Stopping...")
    flush_all_buffers()
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
        'stateful_recorder_v15',
        icon=create_image('green'),
        title="Stateful Recorder (v15-Simple)",
        menu=menu
    )

    if DEBUG_MODE: logging.info("--- Logger Started ---")
    
    icon.run()