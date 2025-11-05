#!/usr/bin/env qqpython3
"""
All-in-One HRC Main System
Runs all components: Voice, OCR, GUI, Arm Control, and Command Matching
Everything in one file for simplicity
"""

import subprocess
import time
import os
import signal
import sys
import threading
import queue
from datetime import datetime

# Fix Qt platform plugin issue
os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Import arm controller
try:
    from tapping_1808 import (
        initialize_arm_system, 
        shutdown_arm_system, 
        process_voice_command,
        process_ocr_command,
        command_processor
    )
    ARM_AVAILABLE = True
    print("[MAIN] ✅ Arm controller imported successfully")
except ImportError as e:
    ARM_AVAILABLE = False
    print(f"[MAIN] ⚠️ Arm controller not available: {e}")

# Script paths
VOICE_SCRIPT = "voice4.py"
OCR_SCRIPT = "ocr4.py"
GUI_SCRIPT = "hrc_gui_dashboard3.py"

class CommandMatcher:
    """Simple command matcher for voice and OCR"""
    
    def __init__(self, timeout=10):
        self.voice_command = None
        self.voice_time = 0
        self.ocr_command = None
        self.ocr_time = 0
        self.timeout = timeout
        self.lock = threading.Lock()
        
        # Valid commands
        self.valid_commands = ['one', 'two', 'three', 'four', 'five', 'home']
        
        # Statistics
        self.stats = {
            'voice_commands': 0,
            'ocr_commands': 0,
            'matched_commands': 0,
            'executed_commands': 0
        }
    
    def add_command(self, command, source):
        """Add a command from voice or OCR"""
        with self.lock:
            # Clean command
            cleaned = self._clean_command(command)
            if not cleaned or cleaned not in self.valid_commands:
                print(f"[MATCHER] ❌ Invalid command: '{command}' from {source}")
                return
            
            current_time = time.time()
            
            if source == "VOICE":
                self.voice_command = cleaned
                self.voice_time = current_time
                self.stats['voice_commands'] += 1
                print(f"[MATCHER] 🎤 Voice: '{cleaned}'")
                
            elif source == "OCR":
                self.ocr_command = cleaned
                self.ocr_time = current_time
                self.stats['ocr_commands'] += 1
                print(f"[MATCHER] 👁️  OCR: '{cleaned}'")
            
            # Check for match
            self._check_match()
    
    def _clean_command(self, command):
        """Clean and normalize command"""
        if not command:
            return None
        
        cleaned = str(command).lower().strip()
        
        # Handle common OCR/voice errors
        mappings = {
            '1': 'one', 'i': 'one', 'l': 'one',
            '2': 'two', 'to': 'two', 'too': 'two',
            '3': 'three', 'tree': 'three',
            '4': 'four', 'for': 'four',
            '5': 'five', 's': 'five',
            '0': 'home', 'zero': 'home', 'o': 'home'
        }
        
        return mappings.get(cleaned, cleaned)
    
    def _check_match(self):
        """Check if voice and OCR commands match"""
        if not self.voice_command or not self.ocr_command:
            return
        
        time_diff = abs(self.voice_time - self.ocr_time)
        
        if self.voice_command == self.ocr_command and time_diff <= self.timeout:
            # MATCH FOUND!
            print(f"[MATCHER] 🎯 MATCH! Command: '{self.voice_command}' (Δt={time_diff:.2f}s)")
            self.stats['matched_commands'] += 1
            
            # Execute command
            success = self._execute_command(self.voice_command)
            if success:
                self.stats['executed_commands'] += 1
                print(f"[MATCHER] ✅ Command '{self.voice_command}' executed successfully!")
            else:
                print(f"[MATCHER] ❌ Command '{self.voice_command}' execution failed!")
            
            # Reset
            self.voice_command = None
            self.ocr_command = None
            self.voice_time = 0
            self.ocr_time = 0
    
    def _execute_command(self, command):
        """Execute the matched command"""
        try:
            if ARM_AVAILABLE:
                print(f"[MATCHER] 🦾 Executing arm command: '{command}'")
                process_voice_command(command)  # Use voice command processor
                return True
            else:
                print(f"[MATCHER] 🔄 SIMULATION: Would execute '{command}'")
                time.sleep(2)  # Simulate execution time
                return True
        except Exception as e:
            print(f"[MATCHER] ❌ Execution error: {e}")
            return False
    
    def cleanup_old_commands(self):
        """Remove old commands that have timed out"""
        with self.lock:
            current_time = time.time()
            
            if self.voice_time and current_time - self.voice_time > self.timeout:
                print(f"[MATCHER] 🧹 Cleaning old voice command: '{self.voice_command}'")
                self.voice_command = None
                self.voice_time = 0
            
            if self.ocr_time and current_time - self.ocr_time > self.timeout:
                print(f"[MATCHER] 🧹 Cleaning old OCR command: '{self.ocr_command}'")
                self.ocr_command = None
                self.ocr_time = 0
    
    def get_stats(self):
        """Get statistics"""
        return self.stats.copy()

class OutputMonitor:
    """Monitor subprocess output for commands"""
    
    def __init__(self, command_matcher):
        self.matcher = command_matcher
        self.monitoring = False
    
    def start_monitoring(self, processes):
        """Start monitoring process outputs"""
        self.monitoring = True
        
        for name, process in processes.items():
            thread = threading.Thread(
                target=self._monitor_process, 
                args=(name, process),
                daemon=True
            )
            thread.start()
    
    def _monitor_process(self, name, process):
        """Monitor a single process output"""
        try:
            while self.monitoring and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    self._process_line(name, line)
                time.sleep(0.01)
        except Exception as e:
            print(f"[MONITOR] Error monitoring {name}: {e}")
    
    def _process_line(self, source, line):
        """Process output line for commands"""
        # Look for command patterns
        if "[COMMAND]" in line:
            try:
                command = line.split("[COMMAND]")[1].strip()
                self.matcher.add_command(command, source.upper())
            except:
                pass
        
        # Print output (filtered)
        if not self._is_noise(line):
            print(f"[{source.upper()}] {line}")
    
    def _is_noise(self, line):
        """Filter out noise lines"""
        noise = ["DEBUG:", "INFO:", "Loading", "Frame rate:", "Buffer"]
        return any(n in line for n in noise)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

class HRCMainSystem:
    """All-in-one HRC system"""
    
    def __init__(self):
        self.processes = {}
        self.command_matcher = CommandMatcher(timeout=15)  # 15 second timeout
        self.output_monitor = OutputMonitor(self.command_matcher)
        self.running = False
        self.stats_thread = None
        self.cleanup_thread = None
    
    def start_everything(self):
        """Start all components"""
        print("🚀 Starting All-in-One HRC System")
        print("=" * 60)
        
        # Initialize arm system
        if ARM_AVAILABLE:
            try:
                initialize_arm_system()
                print("✅ Arm Control System: INITIALIZED")
            except Exception as e:
                print(f"❌ Arm Control System: ERROR - {e}")
        else:
            print("⚠️  Arm Control System: SIMULATION MODE")
        
        # Start all processes
        scripts = {
            "VOICE": VOICE_SCRIPT,
            "OCR": OCR_SCRIPT,
            "GUI": GUI_SCRIPT
        }
        
        for name, script_path in scripts.items():
            if os.path.exists(script_path):
                try:
                    process = subprocess.Popen(
                        [sys.executable, script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    self.processes[name] = process
                    print(f"✅ {name} System: STARTED (PID: {process.pid})")
                except Exception as e:
                    print(f"❌ {name} System: FAILED - {e}")
            else:
                print(f"⚠️  {name} System: FILE NOT FOUND - {script_path}")
        
        # Start output monitoring
        self.output_monitor.start_monitoring(self.processes)
        print("✅ Output Monitoring: STARTED")
        
        # Start background threads
        self.running = True
        
        # Cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Stats thread
        self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        self.stats_thread.start()
        
        print("=" * 60)
        print("🎯 ALL SYSTEMS OPERATIONAL!")
        print("📋 Valid commands: one, two, three, four, five, home")
        print("🔄 Say command AND show to OCR within 15 seconds to execute")
        print("🛑 Press Ctrl+C to stop everything")
        print("=" * 60)
    
    def _cleanup_loop(self):
        """Background cleanup of old commands"""
        while self.running:
            try:
                self.command_matcher.cleanup_old_commands()
                time.sleep(5)
            except:
                pass
    
    def _stats_loop(self):
        """Background statistics reporting"""
        while self.running:
            try:
                time.sleep(30)  # Report every 30 seconds
                stats = self.command_matcher.get_stats()
                print(f"\n[STATS] 📊 Commands - Voice:{stats['voice_commands']}, OCR:{stats['ocr_commands']}, Matched:{stats['matched_commands']}, Executed:{stats['executed_commands']}\n")
            except:
                pass
    
    def monitor_and_restart(self):
        """Keep everything running"""
        try:
            while self.running:
                time.sleep(3)
                
                # Check and restart dead processes
                scripts = {
                    "VOICE": VOICE_SCRIPT,
                    "OCR": OCR_SCRIPT,
                    "GUI": GUI_SCRIPT
                }
                
                for name, script_path in scripts.items():
                    if name in self.processes:
                        process = self.processes[name]
                        if process.poll() is not None:  # Process died
                            print(f"⚠️  {name} died, restarting...")
                            try:
                                new_process = subprocess.Popen(
                                    [sys.executable, script_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    bufsize=1
                                )
                                self.processes[name] = new_process
                                print(f"✅ {name} restarted (PID: {new_process.pid})")
                            except Exception as e:
                                print(f"❌ Failed to restart {name}: {e}")
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown signal received...")
            self.stop_everything()
    
    def stop_everything(self):
        """Stop all systems"""
        print("\n🛑 Stopping All Systems...")
        
        self.running = False
        
        # Stop monitoring
        self.output_monitor.stop_monitoring()
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=3)
                print(f"✅ {name}: STOPPED")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔥 {name}: FORCE KILLED")
            except Exception as e:
                print(f"⚠️  {name}: {e}")
        
        # Shutdown arm system
        if ARM_AVAILABLE:
            try:
                shutdown_arm_system()
                print("✅ Arm System: SHUTDOWN")
            except Exception as e:
                print(f"⚠️  Arm shutdown error: {e}")
        
        # Final stats
        stats = self.command_matcher.get_stats()
        print(f"\n📊 Final Stats:")
        print(f"   Voice Commands: {stats['voice_commands']}")
        print(f"   OCR Commands: {stats['ocr_commands']}")
        print(f"   Matched Commands: {stats['matched_commands']}")
        print(f"   Executed Commands: {stats['executed_commands']}")
        
        print("👋 HRC System stopped successfully!")
    
    def run(self):
        """Main run method"""
        self.start_everything()
        self.monitor_and_restart()

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    sys.exit(0)

def main():
    """Main entry point"""
    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🤖 HRC (Human-Robot Collaboration) All-in-One System")
    print("🎯 Voice + OCR + GUI + Arm Control in One")
    print()
    
    # Create and run the system
    system = HRCMainSystem()
    system.run()

if __name__ == "__main__":
    main()