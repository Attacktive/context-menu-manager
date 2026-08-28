import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
from ..registry_manager import MenuItem, RegistryManager
from .theme import Theme

class AddCustomItemDialog(tk.Toplevel):
	TEMPLATES = [
		('Terminal (WT) Here', 'wt.exe -d "%V"', 'folders'),
		('PowerShell Here', 'powershell.exe -NoExit -Command Set-Location -LiteralPath "%V"', 'folders'),
		('Copy Path to Clip', 'cmd.exe /c echo %1|clip', 'files'),
		('Notepad Edit', 'notepad.exe "%1"', 'files'),
	]

	def __init__(self, parent, on_added: Callable[[str, str, str, Optional[str], Optional[str]], None]):
		super().__init__(parent)
		self.on_added = on_added
		self.title('Add Custom Context Menu Item')
		self.geometry('560x480')
		self.minsize(500, 420)
		self.configure(bg=Theme.BG_DARK)
		self.transient(parent)
		self.grab_set()

		self._setup_ui()

	def _setup_ui(self):
		main_frame = ttk.Frame(self, style='TFrame', padding=20)
		main_frame.pack(fill=tk.BOTH, expand=True)

		title_lbl = ttk.Label(main_frame, text='➕ Create Custom Context Menu Action', style='Header.TLabel')
		title_lbl.pack(anchor=tk.W, pady=(0, 14))

		# Presets frame
		preset_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=10)
		preset_frame.pack(fill=tk.X, pady=(0, 14))

		preset_lbl = ttk.Label(preset_frame, text='⚡ Quick Presets:', style='Card.TLabel', font=Theme.FONT_BOLD)
		preset_lbl.pack(anchor=tk.W, pady=(0, 6))

		preset_btn_row = ttk.Frame(preset_frame, style='Card.TFrame')
		preset_btn_row.pack(fill=tk.X)

		for label, cmd, cat in self.TEMPLATES:
			btn = tk.Button(
				preset_btn_row,
				text=label,
				command=lambda l=label, c=cmd, ct=cat: self._apply_preset(l, c, ct),
				bg=Theme.BG_INPUT,
				fg=Theme.ACCENT_BLUE,
				activebackground=Theme.BORDER_COLOR,
				activeforeground=Theme.TEXT_PRIMARY,
				relief=tk.FLAT,
				font=Theme.FONT_SMALL,
				cursor='hand2',
				padx=8,
				pady=3,
				bd=0
			)
			btn.pack(side=tk.LEFT, padx=3)

		# Form fields
		form_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=14)
		form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

		# Target Category
		ttk.Label(form_frame, text='Target Category:', style='Card.TLabel', font=Theme.FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=6)
		self.category_var = tk.StringVar(value='folders')
		self.cat_combo = ttk.Combobox(
			form_frame,
			textvariable=self.category_var,
			values=['files', 'folders', 'background', 'drives'],
			state='readonly',
			font=Theme.FONT_NORMAL
		)
		self.cat_combo.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=6, padx=(10, 0))

		# Menu Item Name
		ttk.Label(form_frame, text='Menu Label / Name:', style='Card.TLabel', font=Theme.FONT_BOLD).grid(row=1, column=0, sticky=tk.W, pady=6)
		self.name_entry = tk.Entry(
			form_frame,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			insertbackground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_NORMAL
		)
		self.name_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=6, padx=(10, 0), ipady=3)

		# Command
		ttk.Label(form_frame, text='Command Line:', style='Card.TLabel', font=Theme.FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=6)
		self.command_entry = tk.Entry(
			form_frame,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			insertbackground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_NORMAL
		)
		self.command_entry.grid(row=2, column=1, sticky=tk.EW, pady=6, padx=(10, 4), ipady=3)

		browse_cmd_btn = tk.Button(
			form_frame,
			text='Browse...',
			command=self._browse_command,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			activebackground=Theme.BORDER_COLOR,
			relief=tk.FLAT,
			font=Theme.FONT_SMALL,
			cursor='hand2',
			padx=8,
			pady=2,
			bd=0
		)
		browse_cmd_btn.grid(row=2, column=2, sticky=tk.E, pady=6)

		# Icon
		ttk.Label(form_frame, text='Icon (Optional):', style='Card.TLabel').grid(row=3, column=0, sticky=tk.W, pady=6)
		self.icon_entry = tk.Entry(
			form_frame,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			insertbackground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_NORMAL
		)
		self.icon_entry.grid(row=3, column=1, sticky=tk.EW, pady=6, padx=(10, 4), ipady=3)

		browse_icon_btn = tk.Button(
			form_frame,
			text='Browse...',
			command=self._browse_icon,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			activebackground=Theme.BORDER_COLOR,
			relief=tk.FLAT,
			font=Theme.FONT_SMALL,
			cursor='hand2',
			padx=8,
			pady=2,
			bd=0
		)
		browse_icon_btn.grid(row=3, column=2, sticky=tk.E, pady=6)

		# Position
		ttk.Label(form_frame, text='Menu Position:', style='Card.TLabel').grid(row=4, column=0, sticky=tk.W, pady=6)
		self.pos_var = tk.StringVar(value='Default')
		self.pos_combo = ttk.Combobox(
			form_frame,
			textvariable=self.pos_var,
			values=['Default', 'Top', 'Bottom'],
			state='readonly',
			font=Theme.FONT_NORMAL
		)
		self.pos_combo.grid(row=4, column=1, columnspan=2, sticky=tk.EW, pady=6, padx=(10, 0))

		form_frame.columnconfigure(1, weight=1)

		# Buttons row
		btn_frame = ttk.Frame(main_frame, style='TFrame')
		btn_frame.pack(fill=tk.X)

		cancel_btn = ttk.Button(btn_frame, text='Cancel', command=self.destroy)
		cancel_btn.pack(side=tk.RIGHT, padx=(6, 0))

		save_btn = ttk.Button(btn_frame, text='Add to Context Menu', style='Primary.TButton', command=self._on_save)
		save_btn.pack(side=tk.RIGHT)

	def _apply_preset(self, label: str, cmd: str, cat: str):
		self.name_entry.delete(0, tk.END)
		self.name_entry.insert(0, label)
		self.command_entry.delete(0, tk.END)
		self.command_entry.insert(0, cmd)
		self.category_var.set(cat)

	def _browse_command(self):
		filename = filedialog.askopenfilename(
			title='Select Executable / Script',
			filetypes=[
				('Executables and Scripts', '*.exe;*.bat;*.cmd;*.ps1'),
				('All Files', '*.*')
			]
		)

		if filename:
			placeholder = '%1'
			if self.category_var.get() in ('folders', 'background', 'drives'):
				placeholder = '%V'
			self.command_entry.delete(0, tk.END)
			self.command_entry.insert(0, f'"{filename}" "{placeholder}"')
			if not self.name_entry.get().strip():
				base_name = os.path.splitext(os.path.basename(filename))[0]
				self.name_entry.insert(0, f'Open with {base_name.title()}')

	def _browse_icon(self):
		filename = filedialog.askopenfilename(
			title='Select Icon or Executable',
			filetypes=[
				('Icons and Executables', '*.ico;*.exe;*.dll'),
				('All Files', '*.*')
			]
		)

		if filename:
			self.icon_entry.delete(0, tk.END)
			self.icon_entry.insert(0, filename)

	def _on_save(self):
		name = self.name_entry.get().strip()
		command = self.command_entry.get().strip()
		category = self.category_var.get().strip()
		icon = self.icon_entry.get().strip() or None
		pos = self.pos_var.get().strip()
		position = None
		if pos in ('Top', 'Bottom'):
			position = pos

		if not name:
			messagebox.showwarning('Validation', 'Please provide a name for the context menu item.', parent=self)
			return

		if not command:
			messagebox.showwarning('Validation', 'Please provide an executable command.', parent=self)
			return

		self.on_added(category, name, command, icon, position)
		self.destroy()

class ItemDetailsDialog(tk.Toplevel):
	def __init__(self, parent, item: MenuItem, on_open_regedit: Callable[[MenuItem], None]):
		super().__init__(parent)
		self.item = item
		self.on_open_regedit = on_open_regedit
		self.title(f'Details: {item.name}')
		self.geometry('600x460')
		self.minsize(520, 380)
		self.configure(bg=Theme.BG_DARK)
		self.transient(parent)
		self.grab_set()

		self._setup_ui()

	def _setup_ui(self):
		main_frame = ttk.Frame(self, style='TFrame', padding=20)
		main_frame.pack(fill=tk.BOTH, expand=True)

		title_lbl = ttk.Label(main_frame, text=f'📋 {self.item.name}', style='Header.TLabel')
		title_lbl.pack(anchor=tk.W, pady=(0, 10))

		card = ttk.Frame(main_frame, style='Card.TFrame', padding=14)
		card.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

		item_type_label = 'Shell Extension (COM)'
		if self.item.item_type == 'verb':
			item_type_label = 'Shell Verb (Command)'

		scope_label = 'Machine / System'
		if self.item.is_user_level:
			scope_label = 'User'

		status_label = '⚪ Disabled'
		if self.item.is_enabled:
			status_label = '🟢 Enabled'

		cmd_clsid_val = self.item.command or self.item.clsid or 'N/A'

		fields = [
			('Display Name:', self.item.name),
			('Item Type:', item_type_label),
			('Registry Scope:', f'{self.item.root_name} ({scope_label})'),
			('Registry Key:', self.item.key_path),
			('Command / CLSID:', cmd_clsid_val),
			('Status:', status_label)
		]

		for idx, (label, val) in enumerate(fields):
			val_lbl = tk.Text(
				card,
				height=1,
				bg=Theme.BG_INPUT,
				fg=Theme.TEXT_PRIMARY,
				relief=tk.FLAT,
				font=Theme.FONT_NORMAL,
				wrap=tk.WORD,
				bd=0,
				padx=6,
				pady=2
			)

			val_lbl.insert(tk.END, val)
			val_lbl.configure(state='disabled')
			val_lbl.grid(row=idx, column=1, sticky=tk.EW, pady=4, padx=(10, 0))

		card.columnconfigure(1, weight=1)

		# Buttons
		btn_frame = ttk.Frame(main_frame, style='TFrame')
		btn_frame.pack(fill=tk.X)

		close_btn = ttk.Button(btn_frame, text='Close', command=self.destroy)
		close_btn.pack(side=tk.RIGHT, padx=(6, 0))

		regedit_btn = ttk.Button(
			btn_frame,
			text='🔍 Open in RegEdit',
			command=lambda: [self.on_open_regedit(self.item), self.destroy()]
		)
		regedit_btn.pack(side=tk.RIGHT)
