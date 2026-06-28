import socket
from pynput import keyboard
import numpy as np
import sounddevice as sd


UDP_IP = "127.0.0.1"
UDP_TRANSCRIBE_PORT = 9876
UDP_LISTEN_PORT = 9877
TRANSCRIPTION_TOGGLE_COMMAND = {keyboard.Key.ctrl, keyboard.Key.space}
pressed_keys = set()
is_distinct_key_press = True
_recording_active = False

# Used to signal start and end of transcription.
def play_beep(frequency=1000, duration=0.1, sample_rate=44100, volume=0.2):
    """
    Plays a small beep. Mess with the frequency to create distinct sounds.
    
    Precondition:
        None
    
    Postcondition:
        Plays a small beep. It may or may not be audible depending on 
        what parameters you set and your range of human hearing.
    """


    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = volume * np.sin(frequency * t * 2 * np.pi)
    
    sd.play(tone, sample_rate)
    sd.wait()  

# Function that allows for global listening to keyboard.
def global_listen():
    """
    This function globally listens to the keyboard, no matter what application is focused on.
    It will then send this info over to the realtime transcription script via UDP socket.
    
    Precondition:
        For this function to appropriately work, Ghostty must have appropriate computer access.
        You can give Ghostty this by going to System Settings > Privacy & Security > Accessibility.
        Toggle on Ghostty before running this script. MAKE SURE TO TOGGLE GHOSTTY OFF WHEN YOU'RE DONE.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_LISTEN_PORT))

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
                play_beep(frequency=1000)
                udp_socket.sendto("START".encode(), (UDP_IP, UDP_TRANSCRIBE_PORT))
                _recording_active = True
            else:
                udp_socket.sendto("STOP".encode(), (UDP_IP, UDP_TRANSCRIBE_PORT))
                _recording_active = False
                final_text_bytes, _ = udp_socket.recvfrom(4096)
                play_beep(frequency=500)
                print("[Transcribed Text]", final_text_bytes.decode())

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