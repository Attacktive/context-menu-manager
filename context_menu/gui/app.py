"""Main application window and controller for the Windows Context Menu Manager."""

import tkinter as tk
from tkinter import messagebox, ttk

from ..registry_manager import MenuItem, RegistryManager
from ..tweaks import SystemTweaks
from .dialogs import AddCustomItemDialog, ItemDetailsDialog
from .theme import Theme
from .widgets import ItemTable, SearchBar, StatusBar


class ContextMenuApp(tk.Tk):
	"""Main desktop GUI window managing context menu items and system tweaks."""

	def __init__(self) -> None:
		"""Initialize main application window, registry manager, and UI hierarchy."""
		super().__init__()
		self.title('Windows Context Menu Manager')
		self.geometry('1040x700')
		self.minsize(860, 560)

		self.manager = RegistryManager()
		self.items_by_cat: dict[str, list[MenuItem]] = {}
		self.tables_by_cat: dict[str, ItemTable] = {}

		Theme.apply(self)
		self._setup_ui()
		self._bind_shortcuts()
		self.refresh_all()

	def _setup_ui(self) -> None:
		self._setup_header()
		self._setup_toolbar()
		self._setup_notebook()
		self._setup_status_bar()

	def _setup_header(self) -> None:
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

		header_actions = ttk.Frame(header_frame, style='Card.TFrame')
		header_actions.pack(side=tk.RIGHT, fill=tk.Y)

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
			command=self._on_restart_explorer
		)

		restart_exp_btn.pack(side=tk.RIGHT)

	def _setup_toolbar(self) -> None:
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
			command=self._open_add_dialog
		)

		add_btn.pack(side=tk.LEFT, padx=3)

		refresh_btn = ttk.Button(
			btn_group,
			text='🔄 Refresh',
			command=self.refresh_all
		)

		refresh_btn.pack(side=tk.LEFT, padx=3)

	def _setup_notebook(self) -> None:
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

		tweaks_tab = ttk.Frame(self.notebook, style='TFrame', padding=16)
		self.notebook.add(tweaks_tab, text='🛠️ Tweaks & Info')
		self._setup_tweaks_tab(tweaks_tab)

		self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

	def _setup_tweaks_tab(self, parent: ttk.Frame) -> None:
		card = ttk.Frame(parent, style='Card.TFrame', padding=16)
		card.pack(fill=tk.BOTH, expand=True)

		title = ttk.Label(card, text='Windows Context Menu Tweaks & Quick Fixes', style='Header.TLabel')
		title.pack(anchor=tk.W, pady=(0, 10))

		if SystemTweaks.is_windows_11():
			w11_box = ttk.Frame(card, style='Card.TFrame')
			w11_box.pack(fill=tk.X, pady=8)

			w11_msg = (
				'• Windows 11 Full Classic Context Menu: Restores the classic Windows 10 style menu '
				'instantly without needing to click "Show more options" (Shift+F10).'
			)

			w11_lbl = ttk.Label(w11_box, text=w11_msg, style='Card.TLabel')
			w11_lbl.pack(anchor=tk.W)

		exp_box = ttk.Frame(card, style='Card.TFrame')
		exp_box.pack(fill=tk.X, pady=8)

		exp_msg = (
			'• Explorer Cache Flusher: Registry changes take effect immediately, but Explorer '
			'occasionally caches handlers. Click "Restart Explorer" to reload menus cleanly.'
		)

		exp_lbl = ttk.Label(exp_box, text=exp_msg, style='Card.TLabel')
		exp_lbl.pack(anchor=tk.W)

		backup_box = ttk.Frame(card, style='Card.TFrame')
		backup_box.pack(fill=tk.X, pady=8)

		backup_lbl = ttk.Label(
			backup_box,
			text=f'• Safety & Backups: Deleted items are automatically exported to:\n  {self.manager.backup_dir}',
			style='Card.TLabel'
		)

		backup_lbl.pack(anchor=tk.W)

	def _setup_status_bar(self) -> None:
		self.status_bar = StatusBar(
			self,
			on_relaunch_admin=SystemTweaks.relaunch_as_admin
		)

		self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 8))
		self.status_bar.set_admin_status(self.manager.is_admin())

	def _bind_shortcuts(self) -> None:
		self.bind('<F5>', lambda _: self.refresh_all())
		self.bind('<Control-r>', lambda _: self._on_restart_explorer())
		self.bind('<Control-R>', lambda _: self._on_restart_explorer())
		self.bind('<Control-f>', lambda _: self.search_bar.entry.focus_set())
		self.bind('<Control-F>', lambda _: self.search_bar.entry.focus_set())
		self.bind('<Control-n>', lambda _: self._open_add_dialog())
		self.bind('<Control-N>', lambda _: self._open_add_dialog())

	def _get_active_category(self) -> str | None:
		selected_tab_idx = self.notebook.index(self.notebook.select())
		cat_keys = ['files', 'folders', 'background', 'drives']
		if selected_tab_idx < len(cat_keys):
			return cat_keys[selected_tab_idx]

		return None

	def refresh_all(self) -> None:
		"""Rescan all context menu items from the registry and refresh active views."""
		self.items_by_cat = self.manager.scan_all()
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

	def _update_tab_counts(self) -> None:
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

	def _on_search_query_changed(self, query: str) -> None:
		for table in self.tables_by_cat.values():
			table.apply_filter(query)

	def _on_tab_changed(self, _event: tk.Event) -> None:
		query = self.search_bar.get_text()
		active_cat = self._get_active_category()
		if active_cat and active_cat in self.tables_by_cat:
			self.tables_by_cat[active_cat].apply_filter(query)

	def _on_toggle_item(self, item: MenuItem) -> None:
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

	def _on_delete_item(self, item: MenuItem) -> None:
		confirm = messagebox.askyesno(
			'Confirm Delete',
			f'Are you sure you want to delete "{item.name}"?\n\n'
			f'Path: {item.key_path}\n\n'
			'A backup will be automatically saved before deletion.'
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

	def _on_open_regedit(self, item: MenuItem) -> None:
		success, msg = SystemTweaks.open_in_regedit(item.root_name, item.key_path)
		if success:
			self.status_bar.set_message(msg)
		else:
			messagebox.showwarning('RegEdit', msg, parent=self)

	def _on_view_details(self, item: MenuItem) -> None:
		ItemDetailsDialog(self, item, on_open_regedit=self._on_open_regedit)

	def _open_add_dialog(self) -> None:
		AddCustomItemDialog(self, on_added=self._on_add_custom_item)

	def _on_add_custom_item(
		self,
		category: str,
		name: str,
		command: str,
		icon: str | None = None,
		position: str | None = None
	) -> None:
		success, msg = self.manager.add_custom_item(
			category=category,
			name=name,
			command=command,
			icon=icon,
			position=position
		)

		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			SystemTweaks.notify_shell_change()
			self.refresh_all()
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_toggle_win11_classic(self) -> None:
		enable = self.win11_var.get()
		success, msg = SystemTweaks.set_classic_menu_enabled(enable)
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
			ask_restart = messagebox.askyesno(
				'Restart Explorer?',
				f'{msg}\n\nWould you like to restart Windows Explorer now to apply changes?',
				parent=self
			)

			if ask_restart:
				self._on_restart_explorer()
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)

	def _on_restart_explorer(self) -> None:
		success, msg = SystemTweaks.restart_explorer()
		if success:
			self.status_bar.set_message(msg, Theme.ACCENT_GREEN)
		else:
			self.status_bar.set_message(msg, Theme.ACCENT_RED)
			messagebox.showerror('Error', msg, parent=self)
