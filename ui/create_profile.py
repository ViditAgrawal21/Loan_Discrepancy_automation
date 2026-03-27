"""
Create / Edit Profile dialog with 2 sections:
  1. Login Credentials (username, password)
  2. Bank & Application (state, district, bank, branch, FY, app type)

No Section 3 (Activity & Land Details) — not needed for discrepancy management.
Uses ttk Combobox dropdowns with values from portal constants.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from profile_manager import save_profile, load_profile, profile_exists
from utils.constants import STATES, FINANCIAL_YEARS, APPLICATION_TYPES


class CreateProfileWindow(tk.Toplevel):
    """Profile creation/editing dialog with 2 organized sections."""

    def __init__(self, parent, profile_name=None, on_save_callback=None):
        """
        Args:
            parent: Parent Tk window.
            profile_name: If provided, loads existing profile for editing.
            on_save_callback: Called after successful save with (profile_name).
        """
        super().__init__(parent)
        self.title("Edit Profile" if profile_name else "Create Profile")
        self.geometry("580x580")
        self.resizable(False, True)
        self.on_save_callback = on_save_callback

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 580) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")

        # Scrollable frame
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas, padding=20)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling and unbind on destroy
        self._canvas = canvas
        self._mw_binding = canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units")
        )
        self.bind("<Destroy>", self._on_destroy)

        self._widgets = {}
        self._editing = profile_name
        self._build_form()

        # Load existing profile data if editing
        if profile_name:
            self._load_existing(profile_name)

    def _on_destroy(self, event):
        """Unbind mousewheel when this window is destroyed."""
        if event.widget is self:
            try:
                self._canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

    def _build_form(self):
        """Build the 2-section profile form."""
        frame = self.scroll_frame

        # ═══════════════════════════════════════
        # Profile Name
        # ═══════════════════════════════════════
        ttk.Label(frame, text="Profile Name", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        name_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 15))
        self._widgets["profile_name"] = name_entry

        if self._editing:
            name_entry.insert(0, self._editing)
            name_entry.configure(state="disabled")

        # ═══════════════════════════════════════
        # Section 1: Login Credentials
        # ═══════════════════════════════════════
        self._section_header(frame, "Section 1: Login Credentials")

        self._add_entry(frame, "Username", "username")
        self._add_entry(frame, "Password", "password", show="*")

        # ═══════════════════════════════════════
        # Section 2: Bank & Application Details
        # ═══════════════════════════════════════
        self._section_header(frame, "Section 2: Bank & Application Details")

        self._add_combobox(frame, "State", "state", STATES)
        self._add_entry(frame, "District", "district",
                        placeholder="e.g., Nagpur")
        self._add_entry(frame, "Bank Name", "bank",
                        placeholder="e.g., Central Bank Of India")
        self._add_entry(frame, "Branch Name", "branch",
                        placeholder="e.g., MOUDA-CBIN0283909-051421")
        self._add_combobox(frame, "Financial Year", "financial_year", FINANCIAL_YEARS)
        self._add_combobox(frame, "Application Type", "application_type", APPLICATION_TYPES)

        # ═══════════════════════════════════════
        # Buttons
        # ═══════════════════════════════════════
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=20)

        ttk.Button(btn_frame, text="Save Profile", command=self._save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _section_header(self, parent, text):
        """Add a section header with separator."""
        sep = ttk.Separator(parent, orient="horizontal")
        sep.pack(fill="x", pady=(15, 5))
        ttk.Label(parent, text=text, font=("Segoe UI", 11, "bold"),
                  foreground="#1a5276").pack(anchor="w", pady=(0, 10))

    def _add_entry(self, parent, label, key, show=None, placeholder=""):
        """Add a labeled text entry field."""
        ttk.Label(parent, text=label, font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
        entry = ttk.Entry(parent, width=40, font=("Segoe UI", 10), show=show or "")
        entry.pack(fill="x", pady=(0, 5))
        if placeholder:
            entry.insert(0, placeholder)
            entry.configure(foreground="gray")
            entry.bind("<FocusIn>", lambda e, ent=entry, ph=placeholder: self._on_focus_in(ent, ph))
            entry.bind("<FocusOut>", lambda e, ent=entry, ph=placeholder: self._on_focus_out(ent, ph))
        self._widgets[key] = entry

    def _add_combobox(self, parent, label, key, values):
        """Add a labeled dropdown combobox."""
        ttk.Label(parent, text=label, font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
        combo = ttk.Combobox(parent, values=values, width=38, font=("Segoe UI", 10), state="normal")
        combo.pack(fill="x", pady=(0, 5))
        self._widgets[key] = combo

    def _on_focus_in(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(foreground="black")

    def _on_focus_out(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(foreground="gray")

    def _load_existing(self, profile_name):
        """Load existing profile data into form fields."""
        try:
            data = load_profile(profile_name)
            field_map = {
                "username": "username",
                "password": "password",
                "state": "state",
                "district": "district",
                "bank": "bank",
                "branch": "branch",
                "financial_year": "financial_year",
                "application_type": "application_type",
            }
            for data_key, widget_key in field_map.items():
                value = data.get(data_key, "")
                widget = self._widgets.get(widget_key)
                if widget and value:
                    if isinstance(widget, ttk.Combobox):
                        widget.set(value)
                    else:
                        widget.delete(0, "end")
                        widget.insert(0, value)
                        widget.configure(foreground="black")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load profile: {e}", parent=self)

    def _get_value(self, key, placeholders=None):
        """Get value from widget, ignoring placeholder text."""
        widget = self._widgets.get(key)
        if not widget:
            return ""
        val = widget.get().strip()
        if placeholders and val in placeholders:
            return ""
        return val

    def _save(self):
        """Validate and save the profile."""
        placeholders = [
            "e.g., Nagpur",
            "e.g., Central Bank Of India",
            "e.g., MOUDA-CBIN0283909-051421",
        ]

        profile_name = self._get_value("profile_name")
        if not profile_name:
            messagebox.showerror("Error", "Profile Name is required", parent=self)
            return

        username = self._get_value("username")
        password = self._get_value("password")

        if not username:
            messagebox.showerror("Error", "Username is required", parent=self)
            return
        if not password:
            messagebox.showerror("Error", "Password is required", parent=self)
            return

        # Check for duplicate name (only on create, not edit)
        if not self._editing and profile_exists(profile_name):
            messagebox.showerror("Error", f"Profile '{profile_name}' already exists", parent=self)
            return

        data = {
            "username": username,
            "password": password,
            "state": self._get_value("state"),
            "district": self._get_value("district", placeholders),
            "bank": self._get_value("bank", placeholders),
            "branch": self._get_value("branch", placeholders),
            "financial_year": self._get_value("financial_year"),
            "application_type": self._get_value("application_type"),
        }

        try:
            save_profile(profile_name, data)
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved!", parent=self)
            if self.on_save_callback:
                self.on_save_callback(profile_name)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save profile: {e}", parent=self)
