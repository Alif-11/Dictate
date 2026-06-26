import socket
from pynput import keyboard


UDP_IP = "127.0.0.1"
UDP_PORT = 9876
TRANSCRIPTION_TOGGLE_COMMAND = {keyboard.Key.ctrl, keyboard.Key.space}
pressed_keys = set()
is_distinct_key_press = True
_recording_active = False


def global_listen():
    """
    Precondition:
        For this function to appropriately work, Ghostty must have appropriate computer access.
        You can give Ghostty this by going to System Settings > Privacy & Security > Accessibility.
        Toggle on Ghostty before running this script. MAKE SURE TO TOGGLE GHOSTTY OFF WHEN YOU'RE DONE.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def on_press(key):
        global is_distinct_key_press, _recording_active
        
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
            if not _recording_active:
                udp_socket.sendto(b"START", (UDP_IP, UDP_PORT))
                _recording_active = True
            else:
                udp_socket.sendto(b"STOP", (UDP_IP, UDP_PORT))
                _recording_active = False

    def on_release(key):
        global is_distinct_key_press
        
        if key in pressed_keys and key in TRANSCRIPTION_TOGGLE_COMMAND:
            is_distinct_key_press = True
            print(f"Releasing {key}!\n")
            pressed_keys.remove(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    global_listen()