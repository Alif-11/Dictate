from pynput import keyboard

TRANSCRIPTION_TOGGLE_COMMAND = {keyboard.Key.ctrl, keyboard.Key.space}
pressed_keys = set()
is_distinct_key_press = True

def _on_press(key: keyboard.Key):
    global is_distinct_key_press
    
    if key == keyboard.Key.ctrl and key not in pressed_keys:
        print(f"Pressing {key}!\n")
        pressed_keys.add(key)
        
    elif key == keyboard.Key.space and key not in pressed_keys:
        print(f"Pressing {key}!")
        pressed_keys.add(key)
    
    if is_distinct_key_press \
    and (keyboard.Key.space in pressed_keys) \
    and (keyboard.Key.ctrl in pressed_keys):
        is_distinct_key_press = False
        #TODO: Begin transcription

def _on_release(key: keyboard.Key):
    global is_distinct_key_press
    
    if key in pressed_keys and key in TRANSCRIPTION_TOGGLE_COMMAND:
        is_distinct_key_press = True
        print(f"Releasing {key}!\n")
        pressed_keys.remove(key)
        #TODO: End transcription
    
def global_listen():
    with keyboard.Listener(on_press=_on_press, on_release=_on_release) as listener:
        listener.join()

if __name__ == "__main__":
    global_listen()