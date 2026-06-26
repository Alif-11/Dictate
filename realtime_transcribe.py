import collections
import subprocess
import queue
import sys
import tty
import termios
import select
import time
import socket
import numpy as np
import sounddevice as sd
import mlx_whisper


SAMPLE_RATE = 16000
MODEL_NAME = "mlx-community/whisper-large-v3-turbo"
UDP_IP = "127.0.0.1"
UDP_PORT = 9876
raw_audio_queue = queue.Queue()

AVOID_REPEAT_DELAY = 0.4

def audio_callback(indata, frames, time, status):
    raw_audio_queue.put(indata.copy())

def check_udp_signal(udp_socket):
    try:
        data, _ = udp_socket.recvfrom(1024)
        return data.decode()
    except BlockingIOError:
        return None


def _setup_transcription():
    print(f"Warming up MLX model: {MODEL_NAME}...")
    print("See transcription dictionary",mlx_whisper.transcribe(np.zeros(int(SAMPLE_RATE * 0.1), dtype=np.float32), path_or_hf_repo=MODEL_NAME, fp16=True))
    
    subprocess.run(['clear'])
    print("System Ready!")
    print("Press [Ctrl+Space] to START transcription.")
    print("Press [Ctrl+Space] again as soon as you finish talking to STOP.")
    print("Press [Ctrl+C] to exit.\n")

    # Keep track of audio right before space was hit, just to allow transcription software better context
    pre_roll_buffer = collections.deque(maxlen=25)
    speech_frames = []
    recording_active = False
    
    last_cmd_timestamp = 0.0
      

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=0,
        dtype='float32',
        callback=audio_callback
    )

    # Regular terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    return pre_roll_buffer, speech_frames, recording_active, \
        last_cmd_timestamp, stream, old_settings


def transcription_loop():
    """
    Listens to device audio input to transcribe text. Overwrites Appends all transcribed text to `file_path`.
    """
    
    pre_roll_buffer, speech_frames, recording_active, \
        last_cmd_timestamp, stream, old_settings = \
        _setup_transcription()

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setblocking(False)
    udp_socket.bind((UDP_IP, UDP_PORT))

    with stream:
        try:
            
            # Terminal mode shifted to allow for lightning fast spacebar handling
            tty.setcbreak(sys.stdin.fileno())

            while True:
                try:
                    # Snatch frames as they arrive
                    audio_frame_float = raw_audio_queue.get(timeout=0.005)
                except queue.Empty:
                    audio_frame_float = None

                # Process the ongoing live audio capture frame by frame
                if audio_frame_float is not None:
                    audio_frame_float = audio_frame_float.flatten()

                    if not recording_active:
                        pre_roll_buffer.append(audio_frame_float)
                    else:
                        speech_frames.append(audio_frame_float)

                # Check for UDP signal from keyboard listener
                signal = check_udp_signal(udp_socket)
                if signal is None:
                    continue

                current_cmd_timestamp = time.time()
                if current_cmd_timestamp - last_cmd_timestamp < AVOID_REPEAT_DELAY:
                    continue
                
                last_cmd_timestamp = current_cmd_timestamp 

                if signal == "START":
                    # START RECORDING STEP
                    recording_active = True
                    sys.stdout.write(f"\r[RECORDING ACTIVE] - Speak now...")
                    sys.stdout.flush()
                    speech_frames = list(pre_roll_buffer)
                    pre_roll_buffer.clear()
                elif signal == "STOP":
                    # STOP RECORDING STEP
                    sys.stdout.write("\r[DRAINING AUDIO PIPELINE...]")
                    sys.stdout.flush()

                    # Give the audio input listening thread an extra 100ms to dump its last buffers                        
                    time.sleep(0.1)
                    while not raw_audio_queue.empty():
                        extra_frame = raw_audio_queue.get().flatten()
                        speech_frames.append(extra_frame)

                    sys.stdout.write("\r⏳[PROCESSING FINAL TEXT PASS...]")
                    sys.stdout.flush()

                    # Now transcribe the complete file
                    if len(speech_frames) > 0:
                        compiled_audio = np.concatenate(speech_frames)
                        result = mlx_whisper.transcribe(compiled_audio, path_or_hf_repo=MODEL_NAME, fp16=True)
                        final_text = result.get("text", "").strip()

                        sys.stdout.write("\r\033[K") # Clear line
                        if final_text:
                            print(f"[CAPTURED OUTPUT] : {final_text}")
                        else:
                            print("[CAPTURED OUTPUT] : (No clear speech detected)")
                    
                    # Reset states
                    recording_active = False
                    speech_frames = []
                    print(f"\nPress [Ctrl+Space] to begin your next phrase...")

        except KeyboardInterrupt:
            print("\nShutting down transcription engine...")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    transcription_loop()
    
    
