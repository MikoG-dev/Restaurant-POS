"""
generate_license.py — License File Generator
=============================================
Run this script ON THE CLIENT'S MACHINE to generate their license.dat file.
Then place license.dat in the same folder as RestaurantPOS.exe.

Usage:
    python generate_license.py

Or double-click it on the client machine (it will auto-run and show the result).

The generated license.dat is locked to the hardware of the machine it was
run on. If someone copies the EXE to a different machine, the app will refuse
to start and show an error with your contact info.
"""

import hashlib
import subprocess
import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog


# ---------------------------------------------------------------------------
# Hardware info collection (same logic as license_check.py)
# ---------------------------------------------------------------------------

def _run_wmic(query: str) -> str:
    try:
        result = subprocess.check_output(
            query, shell=True, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        lines = result.decode(errors="ignore").strip().splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(("serialnumber", "uuid",
                                                      "processorid", "name",
                                                      "caption")):
                return line
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _get_motherboard_serial() -> str:
    return _run_wmic("wmic baseboard get SerialNumber")

def _get_disk_serial() -> str:
    return _run_wmic("wmic diskdrive get SerialNumber")

def _get_os_machine_id() -> str:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography"
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return value
    except Exception:
        return "UNKNOWN"

def _get_cpu_model() -> str:
    return _run_wmic("wmic cpu get Name")

def _normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("\t", "")

def generate_fingerprint() -> str:
    motherboard = _normalize(_get_motherboard_serial())
    disk        = _normalize(_get_disk_serial())
    machine_id  = _normalize(_get_os_machine_id())
    cpu         = _normalize(_get_cpu_model())
    raw = motherboard + disk + machine_id + cpu
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

def run_gui():
    root = tk.Tk()
    root.title("Restaurant POS — License Generator")
    root.geometry("520x320")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    # Title
    tk.Label(root, text="🔑  License Generator", font=("Segoe UI", 16, "bold"),
             bg="#1e1e2e", fg="#cdd6f4").pack(pady=(20, 4))
    tk.Label(root, text="Generates a license.dat locked to this machine's hardware.",
             font=("Segoe UI", 9), bg="#1e1e2e", fg="#a6adc8").pack()

    # Fingerprint display
    fp_frame = tk.Frame(root, bg="#313244", padx=10, pady=10)
    fp_frame.pack(fill="x", padx=20, pady=16)

    tk.Label(fp_frame, text="Hardware Fingerprint (SHA-256):",
             font=("Segoe UI", 9, "bold"), bg="#313244", fg="#a6adc8").pack(anchor="w")

    fp_var = tk.StringVar(value="Generating...")
    fp_label = tk.Label(fp_frame, textvariable=fp_var, font=("Courier New", 9),
                        bg="#313244", fg="#a6e3a1", wraplength=460, justify="left")
    fp_label.pack(anchor="w", pady=(4, 0))

    # Generate fingerprint
    fingerprint = generate_fingerprint()
    fp_var.set(fingerprint)

    # Status label
    status_var = tk.StringVar(value="")
    status_label = tk.Label(root, textvariable=status_var, font=("Segoe UI", 9),
                            bg="#1e1e2e", fg="#a6e3a1")
    status_label.pack()

    def save_license():
        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            title="Save license.dat",
            initialfile="license.dat",
            defaultextension=".dat",
            filetypes=[("License file", "*.dat"), ("All files", "*.*")]
        )
        if not save_path:
            return
        try:
            with open(save_path, "w") as f:
                f.write(fingerprint)
            status_var.set(f"✓ Saved to: {save_path}")
            status_label.config(fg="#a6e3a1")
            messagebox.showinfo(
                "License Generated",
                f"license.dat saved successfully!\n\n"
                f"Place it in the same folder as RestaurantPOS.exe on this machine."
            )
        except Exception as e:
            status_var.set(f"✗ Error: {e}")
            status_label.config(fg="#f38ba8")

    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(fingerprint)
        status_var.set("✓ Fingerprint copied to clipboard!")
        status_label.config(fg="#89b4fa")

    # Buttons
    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack(pady=12)

    tk.Button(btn_frame, text="💾  Save license.dat", command=save_license,
              font=("Segoe UI", 10, "bold"), bg="#89b4fa", fg="#1e1e2e",
              relief="flat", padx=16, pady=6, cursor="hand2").pack(side="left", padx=8)

    tk.Button(btn_frame, text="📋  Copy Fingerprint", command=copy_to_clipboard,
              font=("Segoe UI", 10), bg="#313244", fg="#cdd6f4",
              relief="flat", padx=16, pady=6, cursor="hand2").pack(side="left", padx=8)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
