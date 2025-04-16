import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import subprocess
import os

class SystemSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Scheduler")
        self.root.geometry("450x550")
        self.root.resizable(False, False)

        # Dark modern theme
        self.root.configure(bg="#1e1e2e")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 11))
        style.configure("TButton", background="#89b4fa", foreground="#1e1e2e", font=("Segoe UI", 10, "bold"), 
                        borderwidth=0, padding=10, focuscolor="#89b4fa")
        style.map("TButton", background=[("active", "#b4befe")])
        style.configure("TCombobox", fieldbackground="#313244", background="#313244", 
                        foreground="#cdd6f4", selectbackground="#45475a", selectforeground="#cdd6f4")
        style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", 
                        insertcolor="#cdd6f4", borderwidth=1)

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="30")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Title
        ttk.Label(self.main_frame, text="Schedule System Action", font=("Segoe UI", 18, "bold"), 
                 foreground="#b4befe").grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Action selection
        ttk.Label(self.main_frame, text="Action:").grid(row=1, column=0, sticky="w", pady=10)
        self.action_var = tk.StringVar(value="Sleep")
        action_combo = ttk.Combobox(self.main_frame, textvariable=self.action_var, 
                                   values=["Sleep", "Shutdown"], state="readonly", width=25)
        action_combo.grid(row=1, column=1, pady=10, sticky="w")

        # Date selection
        ttk.Label(self.main_frame, text="Date (MM/DD/YYYY):").grid(row=2, column=0, sticky="w", pady=10)
        self.date_entry = ttk.Entry(self.main_frame, width=28)
        self.date_entry.grid(row=2, column=1, pady=10, sticky="w")
        self.date_entry.insert(0, datetime.now().strftime("%m/%d/%Y"))

        # Time selection
        ttk.Label(self.main_frame, text="Time (HH:MM AM/PM):").grid(row=3, column=0, sticky="w", pady=10)
        time_frame = ttk.Frame(self.main_frame)
        time_frame.grid(row=3, column=1, sticky="w", pady=10)

        self.hour_entry = ttk.Entry(time_frame, width=5)
        self.hour_entry.insert(0, (datetime.now() + timedelta(hours=1)).strftime("%I").lstrip("0") or "12")
        self.hour_entry.grid(row=0, column=0)

        ttk.Label(time_frame, text=":", font=("Segoe UI", 11)).grid(row=0, column=1)
        
        self.minute_entry = ttk.Entry(time_frame, width=5)
        self.minute_entry.insert(0, (datetime.now() + timedelta(hours=1)).strftime("%M"))
        self.minute_entry.grid(row=0, column=2)

        self.ampm_var = tk.StringVar(value=(datetime.now() + timedelta(hours=1)).strftime("%p"))
        ampm_combo = ttk.Combobox(time_frame, textvariable=self.ampm_var, 
                                 values=["AM", "PM"], state="readonly", width=5)
        ampm_combo.grid(row=0, column=3, padx=(10, 0))

        # Schedule button
        ttk.Button(self.main_frame, text="Schedule Action", command=self.schedule_action).grid(
            row=4, column=0, columnspan=2, pady=40)

        # Center the window
        self.root.eval('tk::PlaceWindow . center')

    def validate_datetime(self, date_str, hour_str, minute_str, ampm):
        try:
            # Combine inputs and validate
            time_str = f"{hour_str.zfill(2)}:{minute_str.zfill(2)} {ampm}"
            datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p")
            return True
        except ValueError:
            return False

    def convert_to_24hr(self, hour, minute, ampm):
        # Convert 12-hour time to 24-hour format
        dt = datetime.strptime(f"{hour.zfill(2)}:{minute.zfill(2)} {ampm}", "%I:%M %p")
        return dt.strftime("%H:%M")

    def schedule_action(self):
        date_str = self.date_entry.get()
        hour_str = self.hour_entry.get()
        minute_str = self.minute_entry.get()
        ampm = self.ampm_var.get()
        action = self.action_var.get()

        if not self.validate_datetime(date_str, hour_str, minute_str, ampm):
            messagebox.showerror("Error", "Invalid date or time format. Use MM/DD/YYYY and HH:MM AM/PM.")
            return

        # Convert to 24-hour format for schtasks
        time_24hr = self.convert_to_24hr(hour_str, minute_str, ampm)
        task_time = f"{date_str}T{time_24hr}:00"

        # Create batch file for the action
        batch_dir = os.path.expanduser("~/App-Data/Local/SystemScheduler")
        os.makedirs(batch_dir, exist_ok=True)
        batch_file = os.path.join(batch_dir, "system_action.bat")

        if action == "Sleep":
            command = 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0'
        else:  # Shutdown
            command = 'shutdown /s /t 0'

        with open(batch_file, 'w') as f:
            f.write(f"@echo off\n{command}")

        # Create scheduled task
        task_name = f"SystemScheduler_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        schtasks_cmd = (
            f'schtasks /create /tn "{task_name}" /tr "{batch_file}" '
            f'/sc once /st {time_24hr} /sd {date_str} /f'
        )

        try:
            result = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                display_time = f"{hour_str.zfill(2)}:{minute_str.zfill(2)} {ampm}"
                messagebox.showinfo("Success", f"{action} scheduled for {date_str} {display_time}")
                self.root.quit()
            else:
                messagebox.showerror("Error", f"Failed to schedule task: {result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = SystemSchedulerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()