#!/usr/bin/env python3
"""
HRC GUI Dashboard with Command Matching Visualization
Integrates with the modified main control system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue
import json
import os
from datetime import datetime
import sys

class HRCDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("HRC Robotic Arm Control Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Queue for thread-safe GUI updates
        self.gui_queue = queue.Queue()
        
        # Data storage
        self.voice_commands = []
        self.ocr_commands = []
        self.matched_commands = []
        self.system_status = {
            'voice_active': False,
            'ocr_active': False,
            'arm_active': False,
            'matcher_active': False
        }
        
        # Current command states
        self.current_voice_command = None
        self.current_ocr_command = None
        self.current_voice_time = None
        self.current_ocr_time = None
        
        # Valid commands
        self.valid_commands = ['one', 'two', 'three', 'four', 'five']
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.start_gui_updater()
        
        # Start monitoring (simulated for demo)
        self.start_monitoring()
    
    def setup_styles(self):
        """Configure custom styles for the GUI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', 
                       background='#1a1a1a', 
                       foreground='#00ff00',
                       font=('Arial', 16, 'bold'))
        
        style.configure('Status.TLabel',
                       background='#2a2a2a',
                       foreground='#ffffff',
                       font=('Arial', 10))
        
        style.configure('Active.TLabel',
                       background='#2a2a2a',
                       foreground='#00ff00',
                       font=('Arial', 10, 'bold'))
        
        style.configure('Inactive.TLabel',
                       background='#2a2a2a',
                       foreground='#ff4444',
                       font=('Arial', 10))
        
        style.configure('Command.TLabel',
                       background='#333333',
                       foreground='#ffffff',
                       font=('Arial', 12, 'bold'))
        
        style.configure('Match.TLabel',
                       background='#004400',
                       foreground='#00ff00',
                       font=('Arial', 14, 'bold'))
        
        style.configure('Mismatch.TLabel',
                       background='#440000',
                       foreground='#ff4444',
                       font=('Arial', 14, 'bold'))
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#1a1a1a')
        title_frame.pack(fill='x', pady=10)
        
        title_label = ttk.Label(title_frame, 
                               text="🤖 HRC Robotic Arm Control Dashboard",
                               style='Title.TLabel')
        title_label.pack()
        
        # Create main container
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left column - System Status
        left_frame = tk.Frame(main_frame, bg='#2a2a2a', relief='raised', bd=2)
        left_frame.pack(side='left', fill='y', padx=5)
        
        self.create_system_status(left_frame)
        
        # Center column - Command Matching
        center_frame = tk.Frame(main_frame, bg='#2a2a2a', relief='raised', bd=2)
        center_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_command_matching(center_frame)
        
        # Right column - Command History
        right_frame = tk.Frame(main_frame, bg='#2a2a2a', relief='raised', bd=2)
        right_frame.pack(side='right', fill='y', padx=5)
        
        self.create_command_history(right_frame)
        
        # Bottom frame - Control buttons
        bottom_frame = tk.Frame(self.root, bg='#1a1a1a')
        bottom_frame.pack(fill='x', pady=10)
        
        self.create_control_buttons(bottom_frame)
    
    def create_system_status(self, parent):
        """Create system status panel"""
        status_title = ttk.Label(parent, text="🔧 System Status", style='Title.TLabel')
        status_title.pack(pady=10)
        
        # Status indicators
        self.status_labels = {}
        
        status_items = [
            ('voice', '🎤 Voice Recognition'),
            ('ocr', '👁 OCR Detection'),
            ('arm', '🦾 Arm Control'),
            ('matcher', '🔗 Command Matcher')
        ]
        
        for key, label in status_items:
            frame = tk.Frame(parent, bg='#2a2a2a')
            frame.pack(fill='x', padx=10, pady=5)
            
            text_label = ttk.Label(frame, text=label, style='Status.TLabel')
            text_label.pack(side='left')
            
            status_label = ttk.Label(frame, text="INACTIVE", style='Inactive.TLabel')
            status_label.pack(side='right')
            
            self.status_labels[key] = status_label
        
        # Separator
        separator = tk.Frame(parent, height=2, bg='#444444')
        separator.pack(fill='x', padx=10, pady=10)
        
        # Valid commands
        commands_title = ttk.Label(parent, text="📝 Valid Commands", style='Title.TLabel')
        commands_title.pack(pady=10)
        
        for cmd in self.valid_commands:
            cmd_frame = tk.Frame(parent, bg='#333333', relief='raised', bd=1)
            cmd_frame.pack(fill='x', padx=10, pady=2)
            
            ttk.Label(cmd_frame, text=cmd.upper(), style='Command.TLabel').pack(pady=5)
    
    def create_command_matching(self, parent):
        """Create command matching visualization"""
        match_title = ttk.Label(parent, text="🔗 Command Matching", style='Title.TLabel')
        match_title.pack(pady=10)
        
        # Current commands frame
        current_frame = tk.Frame(parent, bg='#333333', relief='raised', bd=2)
        current_frame.pack(fill='x', padx=10, pady=10)
        
        # Voice command section
        voice_frame = tk.Frame(current_frame, bg='#333333')
        voice_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(voice_frame, text="🎤 Voice Command:", style='Status.TLabel').pack(side='left')
        self.voice_cmd_label = ttk.Label(voice_frame, text="None", style='Command.TLabel')
        self.voice_cmd_label.pack(side='right')
        
        # OCR command section
        ocr_frame = tk.Frame(current_frame, bg='#333333')
        ocr_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(ocr_frame, text="👁 OCR Command:", style='Status.TLabel').pack(side='left')
        self.ocr_cmd_label = ttk.Label(ocr_frame, text="None", style='Command.TLabel')
        self.ocr_cmd_label.pack(side='right')
        
        # Timeout progress
        timeout_frame = tk.Frame(current_frame, bg='#333333')
        timeout_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="⏰ Timeout:", style='Status.TLabel').pack(side='left')
        
        self.timeout_progress = ttk.Progressbar(timeout_frame, 
                                               length=200, 
                                               mode='determinate',
                                               maximum=100)
        self.timeout_progress.pack(side='right', padx=5)
        
        # Match status
        self.match_status_frame = tk.Frame(parent, bg='#2a2a2a')
        self.match_status_frame.pack(fill='x', padx=10, pady=20)
        
        self.match_status_label = ttk.Label(self.match_status_frame, 
                                          text="⏳ Waiting for commands...", 
                                          style='Status.TLabel')
        self.match_status_label.pack(pady=20)
        
        # Recent matches
        recent_title = ttk.Label(parent, text="✅ Recent Matches", style='Title.TLabel')
        recent_title.pack(pady=(20, 10))
        
        # Matches listbox
        matches_frame = tk.Frame(parent, bg='#333333')
        matches_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.matches_listbox = tk.Listbox(matches_frame, 
                                         bg='#333333', 
                                         fg='#00ff00',
                                         selectbackground='#555555',
                                         font=('Courier', 10))
        self.matches_listbox.pack(fill='both', expand=True)
        
        # Scrollbar for matches
        matches_scrollbar = ttk.Scrollbar(matches_frame, orient='vertical')
        matches_scrollbar.pack(side='right', fill='y')
        self.matches_listbox.config(yscrollcommand=matches_scrollbar.set)
        matches_scrollbar.config(command=self.matches_listbox.yview)
    
    def create_command_history(self, parent):
        """Create command history panel"""
        history_title = ttk.Label(parent, text="📊 Command History", style='Title.TLabel')
        history_title.pack(pady=10)
        
        # Tabs for different command types
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Voice commands tab
        voice_frame = tk.Frame(notebook, bg='#333333')
        notebook.add(voice_frame, text='🎤 Voice')
        
        self.voice_listbox = tk.Listbox(voice_frame, 
                                       bg='#333333', 
                                       fg='#ffffff',
                                       selectbackground='#555555',
                                       font=('Courier', 9))
        self.voice_listbox.pack(fill='both', expand=True)
        
        # OCR commands tab
        ocr_frame = tk.Frame(notebook, bg='#333333')
        notebook.add(ocr_frame, text='👁 OCR')
        
        self.ocr_listbox = tk.Listbox(ocr_frame, 
                                     bg='#333333', 
                                     fg='#ffffff',
                                     selectbackground='#555555',
                                     font=('Courier', 9))
        self.ocr_listbox.pack(fill='both', expand=True)
        
        # Statistics
        stats_frame = tk.Frame(parent, bg='#333333', relief='raised', bd=2)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(stats_frame, text="📈 Statistics", style='Title.TLabel').pack(pady=5)
        
        self.stats_labels = {
            'voice_count': ttk.Label(stats_frame, text="Voice: 0", style='Status.TLabel'),
            'ocr_count': ttk.Label(stats_frame, text="OCR: 0", style='Status.TLabel'),
            'matches_count': ttk.Label(stats_frame, text="Matches: 0", style='Status.TLabel'),
            'success_rate': ttk.Label(stats_frame, text="Success: 0%", style='Status.TLabel')
        }
        
        for label in self.stats_labels.values():
            label.pack(pady=2)
    
    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = tk.Frame(parent, bg='#1a1a1a')
        button_frame.pack()
        
        # Simulate buttons for testing
        simulate_frame = tk.LabelFrame(button_frame, 
                                     text="🧪 Simulation Controls", 
                                     bg='#2a2a2a', 
                                     fg='#ffffff',
                                     font=('Arial', 10, 'bold'))
        simulate_frame.pack(side='left', padx=10)
        
        # Voice simulation buttons
        voice_sim_frame = tk.Frame(simulate_frame, bg='#2a2a2a')
        voice_sim_frame.pack(side='left', padx=10, pady=10)
        
        ttk.Label(voice_sim_frame, text="🎤 Voice:", style='Status.TLabel').pack()
        
        for cmd in self.valid_commands:
            btn = tk.Button(voice_sim_frame, 
                          text=cmd.upper(),
                          command=lambda c=cmd: self.simulate_voice_command(c),
                          bg='#444444',
                          fg='#ffffff',
                          font=('Arial', 8, 'bold'))
            btn.pack(pady=2, fill='x')
        
        # OCR simulation buttons
        ocr_sim_frame = tk.Frame(simulate_frame, bg='#2a2a2a')
        ocr_sim_frame.pack(side='left', padx=10, pady=10)
        
        ttk.Label(ocr_sim_frame, text="👁 OCR:", style='Status.TLabel').pack()
        
        for cmd in self.valid_commands:
            btn = tk.Button(ocr_sim_frame, 
                          text=cmd.upper(),
                          command=lambda c=cmd: self.simulate_ocr_command(c),
                          bg='#444444',
                          fg='#ffffff',
                          font=('Arial', 8, 'bold'))
            btn.pack(pady=2, fill='x')
        
        # Control buttons
        control_frame = tk.LabelFrame(button_frame, 
                                    text="🔧 System Controls", 
                                    bg='#2a2a2a', 
                                    fg='#ffffff',
                                    font=('Arial', 10, 'bold'))
        control_frame.pack(side='right', padx=10)
        
        controls = [
            ("🔄 Reset", self.reset_system),
            ("🧹 Clear History", self.clear_history),
            ("💾 Save Log", self.save_log),
            ("❌ Exit", self.exit_application)
        ]
        
        for text, command in controls:
            btn = tk.Button(control_frame, 
                          text=text,
                          command=command,
                          bg='#444444',
                          fg='#ffffff',
                          font=('Arial', 9, 'bold'))
            btn.pack(pady=5, padx=10, fill='x')
    
    def simulate_voice_command(self, command):
        """Simulate a voice command"""
        self.gui_queue.put(('voice_command', command))
    
    def simulate_ocr_command(self, command):
        """Simulate an OCR command"""
        self.gui_queue.put(('ocr_command', command))
    
    def reset_system(self):
        """Reset the system state"""
        self.gui_queue.put(('reset', None))
    
    def clear_history(self):
        """Clear command history"""
        self.voice_commands.clear()
        self.ocr_commands.clear()
        self.matched_commands.clear()
        self.update_display()
    
    def save_log(self):
        """Save current log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hrc_log_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write(f"HRC Command Log - {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                
                f.write("Voice Commands:\n")
                for cmd in self.voice_commands:
                    f.write(f"  {cmd}\n")
                
                f.write("\nOCR Commands:\n")
                for cmd in self.ocr_commands:
                    f.write(f"  {cmd}\n")
                
                f.write("\nMatched Commands:\n")
                for cmd in self.matched_commands:
                    f.write(f"  {cmd}\n")
            
            messagebox.showinfo("Success", f"Log saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def exit_application(self):
        """Exit the application"""
        self.root.quit()
    
    def start_gui_updater(self):
        """Start the GUI update thread"""
        def update_gui():
            while True:
                try:
                    # Process GUI queue
                    while not self.gui_queue.empty():
                        try:
                            msg_type, data = self.gui_queue.get_nowait()
                            self.process_gui_message(msg_type, data)
                        except queue.Empty:
                            break
                    
                    # Update display
                    self.update_display()
                    
                    # Update timeout progress
                    self.update_timeout_progress()
                    
                    time.sleep(0.1)  # 100ms update rate
                    
                except Exception as e:
                    print(f"GUI Update error: {e}")
        
        update_thread = threading.Thread(target=update_gui)
        update_thread.daemon = True
        update_thread.start()
    
    def process_gui_message(self, msg_type, data):
        """Process messages from the GUI queue"""
        current_time = datetime.now()
        
        if msg_type == 'voice_command':
            self.current_voice_command = data
            self.current_voice_time = current_time
            self.voice_commands.append(f"{current_time.strftime('%H:%M:%S')} - {data}")
            print(f"[GUI] Voice command: {data}")
            
        elif msg_type == 'ocr_command':
            self.current_ocr_command = data
            self.current_ocr_time = current_time
            self.ocr_commands.append(f"{current_time.strftime('%H:%M:%S')} - {data}")
            print(f"[GUI] OCR command: {data}")
            
        elif msg_type == 'reset':
            self.current_voice_command = None
            self.current_ocr_command = None
            self.current_voice_time = None
            self.current_ocr_time = None
            
        # Check for matches
        self.check_command_match()
    
    def check_command_match(self):
        """Check if current commands match"""
        if (self.current_voice_command and 
            self.current_ocr_command and 
            self.current_voice_time and 
            self.current_ocr_time):
            
            # Check if commands are the same
            if self.current_voice_command == self.current_ocr_command:
                # Check if they're within timeout window (10 seconds)
                time_diff = abs((self.current_voice_time - self.current_ocr_time).total_seconds())
                if time_diff <= 10:
                    # Match found!
                    match_time = datetime.now()
                    match_entry = f"{match_time.strftime('%H:%M:%S')} - {self.current_voice_command} (Match!)"
                    self.matched_commands.append(match_entry)
                    
                    # Reset current commands
                    self.current_voice_command = None
                    self.current_ocr_command = None
                    self.current_voice_time = None
                    self.current_ocr_time = None
                    
                    print(f"[GUI] MATCH FOUND: {self.current_voice_command}")
    
    def update_display(self):
        """Update the GUI display"""
        # Update system status
        self.status_labels['voice'].config(text="ACTIVE", style='Active.TLabel')
        self.status_labels['ocr'].config(text="ACTIVE", style='Active.TLabel')
        self.status_labels['arm'].config(text="ACTIVE", style='Active.TLabel')
        self.status_labels['matcher'].config(text="ACTIVE", style='Active.TLabel')
        
        # Update current commands
        self.voice_cmd_label.config(text=self.current_voice_command or "None")
        self.ocr_cmd_label.config(text=self.current_ocr_command or "None")
        
        # Update match status
        if self.current_voice_command and self.current_ocr_command:
            if self.current_voice_command == self.current_ocr_command:
                self.match_status_label.config(text="✅ COMMANDS MATCH!", style='Match.TLabel')
            else:
                self.match_status_label.config(text="❌ Commands don't match", style='Mismatch.TLabel')
        elif self.current_voice_command or self.current_ocr_command:
            self.match_status_label.config(text="⏳ Waiting for matching command...", style='Status.TLabel')
        else:
            self.match_status_label.config(text="⏳ Waiting for commands...", style='Status.TLabel')
        
        # Update history listboxes
        self.voice_listbox.delete(0, tk.END)
        for cmd in self.voice_commands[-20:]:  # Show last 20
            self.voice_listbox.insert(tk.END, cmd)
        
        self.ocr_listbox.delete(0, tk.END)
        for cmd in self.ocr_commands[-20:]:  # Show last 20
            self.ocr_listbox.insert(tk.END, cmd)
        
        # Update matches listbox
        self.matches_listbox.delete(0, tk.END)
        for match in self.matched_commands[-10:]:  # Show last 10
            self.matches_listbox.insert(tk.END, match)
        
        # Update statistics
        voice_count = len(self.voice_commands)
        ocr_count = len(self.ocr_commands)
        matches_count = len(self.matched_commands)
        
        total_commands = voice_count + ocr_count
        success_rate = (matches_count * 2 / total_commands * 100) if total_commands > 0 else 0
        
        self.stats_labels['voice_count'].config(text=f"Voice: {voice_count}")
        self.stats_labels['ocr_count'].config(text=f"OCR: {ocr_count}")
        self.stats_labels['matches_count'].config(text=f"Matches: {matches_count}")
        self.stats_labels['success_rate'].config(text=f"Success: {success_rate:.1f}%")
    
    def update_timeout_progress(self):
        """Update timeout progress bar"""
        if self.current_voice_time or self.current_ocr_time:
            current_time = datetime.now()
            
            # Find the oldest command time
            oldest_time = None
            if self.current_voice_time and self.current_ocr_time:
                oldest_time = min(self.current_voice_time, self.current_ocr_time)
            elif self.current_voice_time:
                oldest_time = self.current_voice_time
            elif self.current_ocr_time:
                oldest_time = self.current_ocr_time
            
            if oldest_time:
                elapsed = (current_time - oldest_time).total_seconds()
                progress = min(elapsed / 10 * 100, 100)  # 10 second timeout
                self.timeout_progress['value'] = progress
                
                # Clear old commands if timed out
                if elapsed > 10:
                    self.current_voice_command = None
                    self.current_ocr_command = None
                    self.current_voice_time = None
                    self.current_ocr_time = None
        else:
            self.timeout_progress['value'] = 0
    
    def start_monitoring(self):
        """Start monitoring system (placeholder for real integration)"""
        # This would integrate with the actual system
        # For now, we'll just activate the system status
        self.system_status = {
            'voice_active': True,
            'ocr_active': True,
            'arm_active': True,
            'matcher_active': True
        }

def main():
    """Main function to run the GUI"""
    try:
        root = tk.Tk()
        app = HRCDashboard(root)
        
        # Handle window close
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()