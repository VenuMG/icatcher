import sounddevice as sd
import queue
import json
import time
import threading
from vosk import Model, KaldiRecognizer
from datetime import datetime
import sys
import os

# Safe path append for both script and interactive environments
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    current_dir = os.getcwd()
sys.path.append(current_dir)


    # Remove direct arm control - main system handles this
ARM_CONTROL_AVAILABLE = False  # Set to False since main system handles control
print("[VOICE] Voice module in detection-only mode - main system handles execution")

# Shared memory for voice commands
shared_voice_command = {
    "value": "",
    "timestamp": None,
    "lock": threading.Lock()
}

class HRCVoiceModule:
    def __init__(self, model_path="/home/venu/vosk_models/vosk-model-small-en-us-0.15"):
        self.q = queue.Queue()
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.target_commands = ["one", "two", "three", "four", "five"]
        self.listening = False
        self.last_command = ""
        self.last_command_time = 0
        self.command_cooldown = 1.0  # seconds
        
        self.audio_params = {
            'samplerate': 16000,
            'blocksize': 4000,
            'dtype': 'int16',
            'channels': 1,
            'callback': self.audio_callback
        }

        print("[VOICE] Voice module initialized")
        print(f"[VOICE] Target commands: {self.target_commands}")
        print("=" * 50)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[VOICE] Audio status: {status}")
        if self.listening:
            self.q.put(bytes(indata))

    def listen_continuous(self, device_id=None):
        print("[VOICE] Starting continuous listening...")
        if device_id is not None:
            self.audio_params["device"] = device_id
            print(f"[VOICE] Using audio device ID: {device_id}")
        self.listening = True

        try:
            with sd.RawInputStream(**self.audio_params):
                while self.listening:
                    try:
                        data = self.q.get(timeout=0.1)
                        if self.rec.AcceptWaveform(data):
                            result = json.loads(self.rec.Result())
                            text = result.get("text", "").strip().lower()
                            if text:
                                self.process_speech(text, is_final=True)
                        else:
                            partial_result = json.loads(self.rec.PartialResult())
                            partial_text = partial_result.get("partial", "").strip().lower()
                            if partial_text:
                                self.process_speech(partial_text, is_final=False)
                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"[VOICE] Error: {e}")
        finally:
            self.listening = False
            print("[VOICE] Listener stopped")

    def process_speech(self, text, is_final=True):
        current_time = time.time()

        if not is_final:
            print(f"[VOICE] Listening: '{text}'", end='\r')
            return

        if text:
            print(f"\n[VOICE] Speech detected: '{text}'")
            matched_command = self.extract_command(text)
            if matched_command:
                if (matched_command != self.last_command or 
                    current_time - self.last_command_time > self.command_cooldown):
                    
                    self.print_detected_command(matched_command)
                    self.update_shared_command(matched_command)

                    self.last_command = matched_command
                    self.last_command_time = current_time
                else:
                    print(f"[VOICE] Cooldown active for '{matched_command}'")
            else:
                print(f"[VOICE] No valid command found in: '{text}'")
        print("-" * 30)

    def extract_command(self, text):
        if text in self.target_commands:
            return text
        for word in text.split():
            if word in self.target_commands:
                return word
        for cmd in self.target_commands:
            if cmd in text:
                return cmd
        return None

    def print_detected_command(self, command):
    # ADD THIS LINE - Main system expects this format
       print(f"[COMMAND] {command}")
    
    # Keep existing output for debugging
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*20} COMMAND DETECTED {'='*20}")
    print(f"[{timestamp}] VOICE COMMAND: '{command.upper()}'")
    print(f"Status: ACTIVE")
    print(f"Action: Ready for execution")
    print("=" * 60)

    def update_shared_command(self, cmd):
        with shared_voice_command["lock"]:
            shared_voice_command["value"] = cmd
            shared_voice_command["timestamp"] = datetime.now()
        print(f"[VOICE] ✓ Command stored in shared memory: '{cmd}'")

    def stop_listening(self):
        print("[VOICE] Stopping voice listener...")
        self.listening = False

# Voice command handler
def handle_voice_command(command):
    """Handle detected voice command"""
    print(f"[VOICE] Processing command: '{command}'")
    if ARM_CONTROL_AVAILABLE:
        process_voice_command(command)
    else:
        print(f"[VOICE] Command '{command}' detected but arm control not available")

# Shared access functions
def get_shared_voice_command():
    with shared_voice_command["lock"]:
        return shared_voice_command["value"], shared_voice_command["timestamp"]

def clear_shared_voice_command():
    with shared_voice_command["lock"]:
        shared_voice_command["value"] = ""
        shared_voice_command["timestamp"] = None

# Run as standalone
if __name__ == "__main__":
    print("Starting Voice Command Module...")
    if ARM_CONTROL_AVAILABLE:
        initialize_arm_system()
    try:
        voice = HRCVoiceModule()
        voice.listen_continuous()
    except KeyboardInterrupt:
        voice.stop_listening()
        print("\n[VOICE] Voice listener terminated by user")
    finally:
        if ARM_CONTROL_AVAILABLE:
            shutdown_arm_system()