"""Reusable UI widgets for search, item table, and status indicators."""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import ClassVar

from ..registry_manager import MenuItem
from .theme import Theme


class SearchBar(tk.Frame):
	"""Search input bar with instant callback and clear button."""

	def __init__(self, parent: tk.Widget, on_search_changed: Callable[[str], None], **kwargs) -> None:
		"""Initialize the search bar with parent container and change callback."""
		super().__init__(parent, bg=Theme.BG_PANEL, **kwargs)
		self.on_search_changed = on_search_changed
		self.search_var = tk.StringVar()
		self.search_var.trace_add('write', self._on_text_change)

		lbl = tk.Label(
			self,
			text='🔍 Search:',
			bg=Theme.BG_PANEL,
			fg=Theme.TEXT_PRIMARY,
			font=Theme.FONT_BOLD
		)

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

	def _on_text_change(self, *_) -> None:
		query = self.search_var.get().strip()
		self.on_search_changed(query)

	def clear(self) -> None:
		"""Clear the search input and refocus the entry box."""
		self.search_var.set('')
		self.entry.focus_set()

	def get_text(self) -> str:
		"""Get the trimmed current search query text."""
		return self.search_var.get().strip()


class ItemTable(tk.Frame):
	"""Treeview table displaying context menu items with status, type, and command."""

	COLUMNS: ClassVar[tuple[str, ...]] = ('status', 'name', 'type', 'root', 'command')

	def __init__(
		self,
		parent: tk.Widget,
		on_toggle: Callable[[MenuItem], None],
		on_delete: Callable[[MenuItem], None],
		on_open_regedit: Callable[[MenuItem], None],
		on_details: Callable[[MenuItem], None],
		**kwargs
	) -> None:
		"""Initialize the item table with row action callbacks."""
		super().__init__(parent, bg=Theme.BG_DARK, **kwargs)
		self.on_toggle = on_toggle
		self.on_delete = on_delete
		self.on_open_regedit = on_open_regedit
		self.on_details = on_details

		self.items_by_row_id: dict[str, MenuItem] = {}
		self.all_items: list[MenuItem] = []
		self.current_filter: str = ''

		self._setup_ui()
		self._setup_context_menu()
	def _setup_ui(self) -> None:
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

	def _setup_context_menu(self) -> None:
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

	def _on_double_click(self, _event: tk.Event) -> None:
		selected = self.get_selected_item()
		if selected is not None:
			self.on_toggle(selected)

	def _on_space_key(self, _event: tk.Event) -> str | None:
		selected = self.get_selected_item()
		if selected is not None:
			self.on_toggle(selected)
			return 'break'

		return None

	def _on_delete_key(self, _event: tk.Event) -> str | None:
		selected = self.get_selected_item()
		if selected is not None:
			self.on_delete(selected)
			return 'break'

		return None

	def _on_right_click(self, event: tk.Event) -> None:
		row_id = self.tree.identify_row(event.y)
		if not row_id:
			return

		self.tree.selection_set(row_id)
		item = self.items_by_row_id.get(row_id)
		if item is None:
			return

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

	def set_items(self, items: list[MenuItem]) -> None:
		"""Populate the table with new items and re-apply active filters."""
		self.all_items = items
		self.apply_filter(self.current_filter)

	def _matches_filter(self, item: MenuItem, query: str) -> bool:
		if not query:
			return True

		lowered = query.lower()
		return (
			lowered in item.name.lower() or
			lowered in item.command.lower() or
			lowered in item.clsid.lower() or
			lowered in item.key_path.lower()
		)

	def apply_filter(self, query: str) -> None:
		"""Filter displayed items by matching against name, command, CLSID, or key path."""
		self.current_filter = query.lower()
		selected_key = self.get_selected_item_id()

		self.tree.delete(*self.tree.get_children())
		self.items_by_row_id.clear()

		for item in self.all_items:
			if not self._matches_filter(item, self.current_filter):
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

	def get_selected_item(self) -> MenuItem | None:
		"""Get the currently selected MenuItem instance, or None if no selection."""
		selected = self.tree.selection()
		if not selected:
			return None

		return self.items_by_row_id.get(selected[0])

	def get_selected_item_id(self) -> str | None:
		"""Get the unique ID of the currently selected item."""
		item = self.get_selected_item()
		if item is not None:
			return item.id

		return None


class StatusBar(tk.Frame):
	"""Application status bar with status messages, item counts, and admin status button."""

	def __init__(self, parent: tk.Widget, on_relaunch_admin: Callable[[], None], **kwargs) -> None:
		"""Initialize status bar with admin elevation handler."""
		super().__init__(parent, bg=Theme.BG_PANEL, **kwargs)
		self.on_relaunch_admin = on_relaunch_admin

		self.status_label = tk.Label(
			self,
			text='Ready',
			bg=Theme.BG_PANEL,
			fg=Theme.TEXT_PRIMARY,
			font=Theme.FONT_NORMAL
		)

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

		self.counts_label = tk.Label(
			self,
			text='0 items',
			bg=Theme.BG_PANEL,
			fg=Theme.TEXT_MUTED,
			font=Theme.FONT_SMALL
		)

		self.counts_label.pack(side=tk.RIGHT, padx=10, pady=6)

	def set_counts(self, total: int, enabled: int, disabled: int) -> None:
		"""Update item count metrics in the status bar."""
		self.counts_label.configure(text=f'Total: {total} | 🟢 {enabled} | ⚪ {disabled}')

	def set_admin_status(self, is_admin: bool) -> None:
		"""Update admin privilege badge display."""
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

	def set_message(self, message: str, color: str | None = None) -> None:
		"""Set status bar message with optional highlight color."""
		self.status_label.configure(text=message)
		if color:
			self.status_label.configure(foreground=color)
		else:
			self.status_label.configure(foreground=Theme.TEXT_PRIMARY)
