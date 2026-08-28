import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
from ..registry_manager import RegistryManager, MenuItem
from ..tweaks import SystemTweaks
from .theme import Theme
from .widgets import SearchBar, ItemTable, StatusBar
from .dialogs import AddCustomItemDialog, ItemDetailsDialog

class ContextMenuApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('Windows Context Menu Manager')
		self.geometry('1040x700')
		self.minsize(860, 560)

		self.manager = RegistryManager()
		self.items_by_cat: Dict[str, List[MenuItem]] = {}
		self.tables_by_cat: Dict[str, ItemTable] = {}

		Theme.apply(self)
		self._setup_ui()
		self._bind_shortcuts()
		self.refresh_all()

	def _setup_ui(self):
		# Header Panel
		header_frame = ttk.Frame(self, style='Card.TFrame', padding=(16, 12))
		header_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

		title_box = ttk.Frame(header_frame, style='Card.TFrame')
		title_box.pack(side=tk.LEFT, fill=tk.Y)

		title_lbl = ttk.Label(
			title_box,
			text='⚡ Windows Context Menu Manager',
			style='Header.TLabel',
			font=Theme.FONT_TITLE
		)

		title_lbl.pack(anchor=tk.W)

		sub_lbl = ttk.Label(
			title_box,
			text='De-clutter, disable, enable, and customize right-click menus without registry headaches.',
			style='CardMuted.TLabel'
		)

		sub_lbl.pack(anchor=tk.W, pady=(2, 0))

		# Header Right Action Buttons
		header_actions = ttk.Frame(header_frame, style='Card.TFrame')
		header_actions.pack(side=tk.RIGHT, fill=tk.Y)

		# Win 11 Classic Menu Toggle
		if SystemTweaks.is_windows_11():
			self.win11_var = tk.BooleanVar(value=SystemTweaks.is_classic_menu_enabled())
			self.win11_chk = ttk.Checkbutton(
				header_actions,
				text='Classic Win 10 Menu (No "Show More")',
				variable=self.win11_var,
				command=self._on_toggle_win11_classic,
				style='TCheckbutton'
			)

			self.win11_chk.pack(side=tk.LEFT, padx=(0, 14))

		restart_exp_btn = ttk.Button(
			header_actions,
			text='🔄 Restart Explorer',
			style='Primary.TButton',
		)

		restart_exp_btn.pack(side=tk.RIGHT)

		# Toolbar & Search Row
		toolbar_frame = ttk.Frame(self, style='TFrame')
		toolbar_frame.pack(fill=tk.X, padx=12, pady=6)

		self.search_bar = SearchBar(toolbar_frame, on_search_changed=self._on_search_query_changed)
		self.search_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

		btn_group = ttk.Frame(toolbar_frame, style='TFrame')
		btn_group.pack(side=tk.RIGHT)

		add_btn = ttk.Button(
			btn_group,
			text='➕ Add Custom Item',
			style='Success.TButton',
		)

		add_btn.pack(side=tk.LEFT, padx=3)

		refresh_btn = ttk.Button(
			btn_group,
			text='🔄 Refresh',
		)

		refresh_btn.pack(side=tk.LEFT, padx=3)

		# Notebook Tabs
		self.notebook = ttk.Notebook(self)
		self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

		cat_tabs = [
			('files', '📄 All Files (*)'),
			('folders', '📁 Folders & Directories'),
			('background', '🖥️ Desktop & Background'),
			('drives', '💾 Drives')
		]

		for cat_key, tab_title in cat_tabs:
			tab_frame = ttk.Frame(self.notebook, style='TFrame', padding=6)
			self.notebook.add(tab_frame, text=tab_title)

			table = ItemTable(
				tab_frame,
				on_toggle=self._on_toggle_item,
				on_delete=self._on_delete_item,
				on_open_regedit=self._on_open_regedit,
				on_details=self._on_view_details
			)

			table.pack(fill=tk.BOTH, expand=True)
			self.tables_by_cat[cat_key] = table

		# Tweaks & Tools Tab
		tweaks_tab = ttk.Frame(self.notebook, style='TFrame', padding=16)
		self.notebook.add(tweaks_tab, text='🛠️ Tweaks & Info')
		self._setup_tweaks_tab(tweaks_tab)

		self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

		# Status Bar
		self.status_bar = StatusBar(
			self,
			on_relaunch_admin=SystemTweaks.relaunch_as_admin
		)

		self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 8))
		self.status_bar.set_admin_status(self.manager.is_admin())

	def _setup_tweaks_tab(self, parent):
		card = ttk.Frame(parent, style='Card.TFrame', padding=16)
		card.pack(fill=tk.BOTH, expand=True)

		title = ttk.Label(card, text='Windows Context Menu Tweaks & Quick Fixes', style='Header.TLabel')
		title.pack(anchor=tk.W, pady=(0, 10))

		# Win 11 Classic Menu explanation
		if SystemTweaks.is_windows_11():
			w11_box = ttk.Frame(card, style='Card.TFrame')
			w11_box.pack(fill=tk.X, pady=8)

			w11_lbl = ttk.Label(
				w11_box,
				text='• Windows 11 Full Classic Context Menu: Restores the classic Windows 10 style menu instantly without needing to click "Show more options" (Shift+F10).',
				style='Card.TLabel',
			)

			w11_lbl.pack(anchor=tk.W)

		exp_box = ttk.Frame(card, style='Card.TFrame')
		exp_box.pack(fill=tk.X, pady=8)

		exp_lbl = ttk.Label(
			exp_box,
			text='• Explorer Cache Flusher: Registry changes usually take effect immediately, but Windows Explorer occasionally caches menu handlers. Click "Restart Explorer" at any time to reload menus completely.',
			style='Card.TLabel',
		)

		exp_lbl.pack(anchor=tk.W)

		backup_box = ttk.Frame(card, style='Card.TFrame')
		backup_box.pack(fill=tk.X, pady=8)

		backup_lbl = ttk.Label(
			backup_box,
			text=f'• Safety & Backups: Every deleted item is automatically backed up as JSON in:\n  {self.manager.backup_dir}',
			style='Card.TLabel',
		)

		backup_lbl.pack(anchor=tk.W)

	def _bind_shortcuts(self):
		self.bind('<F5>', lambda e: self.refresh_all())
		self.bind('<Control-r>', lambda e: self._on_restart_explorer())
		self.bind('<Control-R>', lambda e: self._on_restart_explorer())
		self.bind('<Control-f>', lambda e: self.search_bar.entry.focus_set())
		self.bind('<Control-F>', lambda e: self.search_bar.entry.focus_set())
		self.bind('<Control-n>', lambda e: self._open_add_dialog())
		self.bind('<Control-N>', lambda e: self._open_add_dialog())

	def _get_active_category(self) -> Optional[str]:
		selected_tab_idx = self.notebook.index(self.notebook.select())
		cat_keys = ['files', 'folders', 'background', 'drives']
		if selected_tab_idx < len(cat_keys):
			return cat_keys[selected_tab_idx]
		return None

	def refresh_all(self):
		self.items_by_cat = self.manager.scan_all()
		query = self.search_bar.get_text()

		total_items = 0
		enabled_items = 0
		disabled_items = 0

		for cat_key, table in self.tables_by_cat.items():
			items = self.items_by_cat.get(cat_key, [])
			table.set_items(items)

			total_items += len(items)
			for item in items:
				if item.is_enabled:
					enabled_items += 1
				else:
					disabled_items += 1

		self._update_tab_counts()
		self.status_bar.set_counts(total_items, enabled_items, disabled_items)
		self.status_bar.set_message('Refreshed all context menu entries.')

	def _update_tab_counts(self):
		cat_keys = ['files', 'folders', 'background', 'drives']
		cat_titles = [
			'📄 All Files',
			'📁 Folders',
			'🖥️ Background',
			'💾 Drives'
		]
		for idx, cat_key in enumerate(cat_keys):
			items = self.items_by_cat.get(cat_key, [])
			count = len(items)
			self.notebook.tab(idx, text=f'{cat_titles[idx]} ({count})')

	def _on_search_query_changed(self, query: str):
		for table in self.tables_by_cat.values():
			table.apply_filter(query)

	def _on_tab_changed(self, event):
		query = self.search_bar.get_text()
		active_cat = self._get_active_category()
		if active_cat and active_cat in self.tables_by_cat:
			self.tables_by_cat[active_cat].apply_filter(query)

	def _on_toggle_item(self, item: MenuItem):
		new_state = not item.is_enabled
		success, msg = self.manager.set_item_enabled(item, new_state)
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			SystemTweaks.notify_shell_change()
			active_cat = self._get_active_category()
			if active_cat and active_cat in self.tables_by_cat:
				self.tables_by_cat[active_cat].apply_filter(self.search_bar.get_text())
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_delete_item(self, item: MenuItem):
		confirm = messagebox.askyesno(
			'Confirm Delete',
			f'Are you sure you want to delete "{item.name}"?\n\n'
			f'Path: {item.key_path}\n\n'
			'A backup will be automatically saved before deletion.',
		)

		if not confirm:
			return

		success, msg = self.manager.delete_item(item)
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			SystemTweaks.notify_shell_change()
			self.refresh_all()
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_open_regedit(self, item: MenuItem):
		success, msg = SystemTweaks.open_in_regedit(item.root_name, item.key_path)
		if success:
			self.status_bar.set_message(msg)
		else:
			messagebox.showwarning('RegEdit', msg, parent=self)

	def _on_view_details(self, item: MenuItem):
		ItemDetailsDialog(self, item, on_open_regedit=self._on_open_regedit)

	def _open_add_dialog(self):
		AddCustomItemDialog(self, on_added=self._on_add_custom_item)

	def _on_add_custom_item(
		self,
		category: str,
		name: str,
		command: str,
		icon: Optional[str] = None,
		position: Optional[str] = None
	):
		success, msg = self.manager.add_custom_item(category, name, command, icon, position)
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			SystemTweaks.notify_shell_change()
			self.refresh_all()
			messagebox.showinfo('Success', msg, parent=self)
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_toggle_win11_classic(self):
		enable = self.win11_var.get()
		success, msg = SystemTweaks.set_classic_menu_enabled(enable)
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			ask_restart = messagebox.askyesno(
				'Restart Explorer?',
				f'{msg}\n\nWould you like to restart Windows Explorer now to apply changes?',
			)

			if ask_restart:
				self._on_restart_explorer()
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_restart_explorer(self):
		success, msg = SystemTweaks.restart_explorer()
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)
