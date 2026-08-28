import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional, Dict
from ..registry_manager import MenuItem
from .theme import Theme

class SearchBar(ttk.Frame):
	def __init__(self, parent, on_search_changed: Callable[[str], None], **kwargs):
		super().__init__(parent, style='Card.TFrame', **kwargs)
		self.on_search_changed = on_search_changed
		self.search_var = tk.StringVar()
		self.search_var.trace_add('write', self._on_text_change)

		lbl = ttk.Label(self, text='🔍 Search:', style='Card.TLabel', font=Theme.FONT_BOLD)
		lbl.pack(side=tk.LEFT, padx=(10, 6), pady=8)

		self.entry = tk.Entry(
			self,
			textvariable=self.search_var,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_PRIMARY,
			insertbackground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_NORMAL
		)

		self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=8, ipady=3)

		self.clear_btn = tk.Button(
			self,
			text='✖',
			command=self.clear,
			bg=Theme.BG_INPUT,
			fg=Theme.TEXT_MUTED,
			activebackground=Theme.BORDER_COLOR,
			activeforeground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_SMALL,
			cursor='hand2',
			padx=8,
			pady=2,
			bd=0
		)

		self.clear_btn.pack(side=tk.RIGHT, padx=(4, 10), pady=8)

	def _on_text_change(self, *args):
		query = self.search_var.get().strip()
		self.on_search_changed(query)

	def clear(self):
		self.search_var.set('')
		self.entry.focus_set()

	def get_text(self) -> str:
		return self.search_var.get().strip()

class ItemTable(ttk.Frame):
	COLUMNS = ('status', 'name', 'type', 'root', 'command')

	def __init__(
		self,
		parent,
		on_toggle: Callable[[MenuItem], None],
		on_delete: Callable[[MenuItem], None],
		on_open_regedit: Callable[[MenuItem], None],
		on_details: Callable[[MenuItem], None],
		**kwargs
	):
		super().__init__(parent, **kwargs)
		self.on_toggle = on_toggle
		self.on_delete = on_delete
		self.on_open_regedit = on_open_regedit
		self.on_details = on_details

		self.items_by_row_id: Dict[str, MenuItem] = {}
		self.all_items: List[MenuItem] = []
		self.current_filter: str = ''

		self._setup_ui()
		self._setup_context_menu()

	def _setup_ui(self):
		self.tree = ttk.Treeview(
			self,
			columns=self.COLUMNS,
			show='headings',
			selectmode='browse'
		)

		self.tree.heading('status', text='Status', anchor=tk.CENTER)
		self.tree.heading('name', text='Name', anchor=tk.W)
		self.tree.heading('type', text='Type', anchor=tk.CENTER)
		self.tree.heading('root', text='Scope', anchor=tk.CENTER)
		self.tree.heading('command', text='Command / CLSID', anchor=tk.W)

		self.tree.column('status', width=90, minwidth=80, stretch=False, anchor=tk.CENTER)
		self.tree.column('name', width=220, minwidth=140, stretch=True)
		self.tree.column('type', width=80, minwidth=70, stretch=False, anchor=tk.CENTER)
		self.tree.column('root', width=70, minwidth=60, stretch=False, anchor=tk.CENTER)
		self.tree.column('command', width=380, minwidth=200, stretch=True)

		self.tree.tag_configure('enabled', foreground=Theme.ACCENT_GREEN)
		self.tree.tag_configure('disabled', foreground=Theme.TEXT_DISABLED)

		scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=scrollbar.set)

		self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		self.tree.bind('<Double-1>', self._on_double_click)
		self.tree.bind('<Button-3>', self._on_right_click)
		self.tree.bind('<space>', self._on_space_key)
		self.tree.bind('<Delete>', self._on_delete_key)

	def _setup_context_menu(self):
		self.context_menu = tk.Menu(
			self,
			tearoff=0,
			bg=Theme.BG_CARD,
			fg=Theme.TEXT_PRIMARY,
			activebackground=Theme.ACCENT_BLUE,
			activeforeground='#11111b',
			font=Theme.FONT_NORMAL,
			relief=tk.FLAT,
			bd=1
		)

	def _on_double_click(self, event):
		selected = self.get_selected_item()
		if selected is not None:
			self.on_toggle(selected)

	def _on_space_key(self, event):
		selected = self.get_selected_item()
		if selected is not None:
			self.on_toggle(selected)
			return 'break'

	def _on_delete_key(self, event):
		selected = self.get_selected_item()
		if selected is not None:
			self.on_delete(selected)
			return 'break'

	def _on_right_click(self, event):
		row_id = self.tree.identify_row(event.y)
		if row_id:
			self.tree.selection_set(row_id)
			item = self.items_by_row_id.get(row_id)
			if item is not None:
				self.context_menu.delete(0, tk.END)
				toggle_label = '🟢 Enable Item'
				if item.is_enabled:
					toggle_label = '⚪ Disable Item'

				self.context_menu.add_command(label=toggle_label, command=lambda: self.on_toggle(item))
				self.context_menu.add_separator()
				self.context_menu.add_command(label='🔍 Open in RegEdit', command=lambda: self.on_open_regedit(item))
				self.context_menu.add_command(label='📋 View Details', command=lambda: self.on_details(item))
				self.context_menu.add_separator()
				self.context_menu.add_command(label='🗑️ Delete Item (with Backup)', command=lambda: self.on_delete(item))
				self.context_menu.post(event.x_root, event.y_root)

	def set_items(self, items: List[MenuItem]):
		self.all_items = items
		self.apply_filter(self.current_filter)

	def apply_filter(self, query: str):
		self.current_filter = query.lower()
		selected_key = self.get_selected_item_id()

		self.tree.delete(*self.tree.get_children())
		self.items_by_row_id.clear()

		for idx, item in enumerate(self.all_items):
			if self.current_filter:
				matches = (
					self.current_filter in item.name.lower() or
					self.current_filter in item.command.lower() or
					self.current_filter in item.clsid.lower() or
					self.current_filter in item.key_path.lower()
				)

				if not matches:
					continue

			status_text = '⚪ Disabled'
			tag = 'disabled'
			if item.is_enabled:
				status_text = '🟢 Enabled'
				tag = 'enabled'

			type_text = 'ShellEx'
			if item.item_type == 'verb':
				type_text = 'Verb'

			row_id = self.tree.insert(
				'',
				tk.END,
				values=(status_text, item.name, type_text, item.root_name, item.command),
				tags=(tag,)
			)

			self.items_by_row_id[row_id] = item

			if selected_key and item.id == selected_key:
				self.tree.selection_set(row_id)
				self.tree.see(row_id)

	def get_selected_item(self) -> Optional[MenuItem]:
		selected = self.tree.selection()
		if not selected:
			return None
		return self.items_by_row_id.get(selected[0])

	def get_selected_item_id(self) -> Optional[str]:
		item = self.get_selected_item()
		if item is not None:
			return item.id
		return None

class StatusBar(ttk.Frame):
	def __init__(self, parent, on_relaunch_admin: Callable[[], None], **kwargs):
		super().__init__(parent, style='Card.TFrame', **kwargs)
		self.on_relaunch_admin = on_relaunch_admin

		self.status_label = ttk.Label(self, text='Ready', style='Card.TLabel')
		self.status_label.pack(side=tk.LEFT, padx=10, pady=6)

		self.admin_btn = tk.Button(
			self,
			text='👤 User Mode (Click to Elevate)',
			command=self.on_relaunch_admin,
			bg=Theme.BG_INPUT,
			fg=Theme.ACCENT_ORANGE,
			activebackground=Theme.BORDER_COLOR,
			activeforeground=Theme.TEXT_PRIMARY,
			relief=tk.FLAT,
			font=Theme.FONT_SMALL,
			cursor='hand2',
			padx=8,
			pady=2,
			bd=0
		)

		self.admin_btn.pack(side=tk.RIGHT, padx=10, pady=4)

		self.counts_label = ttk.Label(self, text='0 items', style='CardMuted.TLabel')
		self.counts_label.pack(side=tk.RIGHT, padx=10, pady=6)

	def set_counts(self, total: int, enabled: int, disabled: int):
		self.counts_label.configure(text=f'Total: {total} | 🟢 {enabled} | ⚪ {disabled}')

	def set_admin_status(self, is_admin: bool):
		if is_admin:
			self.admin_btn.configure(
				text='🛡️ Administrator Mode',
				fg=Theme.ACCENT_GREEN,
				state=tk.DISABLED,
				cursor='arrow'
			)
		else:
			self.admin_btn.configure(
				text='👤 User Mode (Click to Elevate)',
				fg=Theme.ACCENT_ORANGE,
				state=tk.NORMAL,
				cursor='hand2'
			)

	def set_message(self, message: str, color: Optional[str] = None):
		self.status_label.configure(text=message)
		if color:
			self.status_label.configure(foreground=color)
		else:
			self.status_label.configure(foreground=Theme.TEXT_PRIMARY)
