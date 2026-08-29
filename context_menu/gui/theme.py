"""Modern dark theme styling for Tkinter and ttk widgets."""

import tkinter as tk
from tkinter import ttk
from typing import ClassVar


class Theme:
	"""Modern Fluent / Slate Dark Palette configuration."""

	BG_DARK: ClassVar[str] = '#181825'
	BG_PANEL: ClassVar[str] = '#1e1e2e'
	BG_CARD: ClassVar[str] = '#252538'
	BG_INPUT: ClassVar[str] = '#313244'
	BORDER_COLOR: ClassVar[str] = '#45475a'

	TEXT_PRIMARY: ClassVar[str] = '#cdd6f4'
	TEXT_MUTED: ClassVar[str] = '#a6adc8'
	TEXT_DISABLED: ClassVar[str] = '#6c7086'

	ACCENT_BLUE: ClassVar[str] = '#89b4fa'
	ACCENT_HOVER: ClassVar[str] = '#b4befe'
	ACCENT_GREEN: ClassVar[str] = '#a6e3a1'
	ACCENT_RED: ClassVar[str] = '#f38ba8'
	ACCENT_ORANGE: ClassVar[str] = '#fab387'
	ACCENT_PURPLE: ClassVar[str] = '#cba6f7'

	FONT_FAMILY: ClassVar[str] = 'Segoe UI'
	FONT_TITLE: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 14, 'bold')
	FONT_SUBTITLE: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 10, 'normal')
	FONT_HEADER: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 11, 'bold')
	FONT_NORMAL: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 10, 'normal')
	FONT_BOLD: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 10, 'bold')
	FONT_SMALL: ClassVar[tuple[str, int, str]] = (FONT_FAMILY, 9, 'normal')
	FONT_CODE: ClassVar[tuple[str, int, str]] = ('Consolas', 9, 'normal')

	@classmethod
	def apply(cls, root: tk.Tk) -> None:
		"""Apply the modern dark theme styling to the given Tk root window."""
		root.configure(bg=cls.BG_DARK)
		style = ttk.Style(root)

		try:
			style.theme_use('clam')
		except tk.TclError:
			pass

		cls._apply_frames_and_labels(style)
		cls._apply_buttons(style)
		cls._apply_notebook_and_treeview(style)
		cls._apply_inputs_and_scrollbars(style)

	@classmethod
	def _apply_frames_and_labels(cls, style: ttk.Style) -> None:
		style.configure('TFrame', background=cls.BG_DARK)
		style.configure('Card.TFrame', background=cls.BG_PANEL, relief='flat')
		style.configure('Border.TFrame', background=cls.BORDER_COLOR)

		style.configure('TLabel', background=cls.BG_DARK, foreground=cls.TEXT_PRIMARY, font=cls.FONT_NORMAL)
		style.configure('Card.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_PRIMARY, font=cls.FONT_NORMAL)
		style.configure('Muted.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_MUTED, font=cls.FONT_SMALL)
		style.configure('Header.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_PRIMARY, font=cls.FONT_HEADER)

	@classmethod
	def _apply_buttons(cls, style: ttk.Style) -> None:
		style.configure(
			'TButton',
			background=cls.BG_INPUT,
			foreground=cls.TEXT_PRIMARY,
			font=cls.FONT_NORMAL,
			borderwidth=0,
			focuscolor='none',
			padding=(10, 6)
		)

		style.map(
			'TButton',
			background=[('active', cls.BORDER_COLOR), ('pressed', cls.BG_CARD)],
			foreground=[('active', '#ffffff')]
		)

		style.configure(
			'Primary.TButton',
			background=cls.ACCENT_BLUE,
			foreground='#11111b',
			font=cls.FONT_BOLD,
			borderwidth=0,
			focuscolor='none',
			padding=(12, 6)
		)

		style.map(
			'Primary.TButton',
			background=[('active', cls.ACCENT_HOVER), ('pressed', cls.ACCENT_BLUE)]
		)

		style.configure(
			'Danger.TButton',
			background=cls.ACCENT_RED,
			foreground='#11111b',
			font=cls.FONT_BOLD,
			borderwidth=0,
			focuscolor='none',
			padding=(10, 6)
		)

		style.map(
			'Danger.TButton',
			background=[('active', '#f5c2e7'), ('pressed', cls.ACCENT_RED)]
		)

		style.configure(
			'Success.TButton',
			background=cls.ACCENT_GREEN,
			foreground='#11111b',
			font=cls.FONT_BOLD,
			borderwidth=0,
			focuscolor='none',
			padding=(10, 6)
		)

		style.map(
			'Success.TButton',
			background=[('active', '#a6e3a1'), ('pressed', cls.ACCENT_GREEN)]
		)

	@classmethod
	def _apply_notebook_and_treeview(cls, style: ttk.Style) -> None:
		style.configure(
			'TNotebook',
			background=cls.BG_DARK,
			borderwidth=0,
			tabmargins=(0, 0, 0, 0)
		)

		style.configure(
			'TNotebook.Tab',
			background=cls.BG_PANEL,
			foreground=cls.TEXT_MUTED,
			font=cls.FONT_BOLD,
			padding=(14, 8),
			borderwidth=0
		)

		style.map(
			'TNotebook.Tab',
			background=[('selected', cls.BG_CARD), ('active', cls.BORDER_COLOR)],
			foreground=[('selected', cls.ACCENT_BLUE), ('active', cls.TEXT_PRIMARY)],
			focuscolor=[('selected', 'none')]
		)

		style.configure(
			'Treeview',
			background=cls.BG_PANEL,
			foreground=cls.TEXT_PRIMARY,
			fieldbackground=cls.BG_PANEL,
			font=cls.FONT_NORMAL,
			rowheight=28,
			borderwidth=0
		)

		style.configure(
			'Treeview.Heading',
			background=cls.BG_INPUT,
			foreground=cls.TEXT_PRIMARY,
			font=cls.FONT_BOLD,
			relief='flat',
			padding=(6, 6)
		)

		style.map(
			'Treeview.Heading',
			background=[('active', cls.BORDER_COLOR)]
		)

	@classmethod
	def _apply_inputs_and_scrollbars(cls, style: ttk.Style) -> None:
		style.configure(
			'TEntry',
			fieldbackground=cls.BG_INPUT,
			foreground=cls.TEXT_PRIMARY,
			insertcolor=cls.TEXT_PRIMARY,
			borderwidth=0,
			padding=(8, 6)
		)

		style.configure(
			'TCheckbutton',
			background=cls.BG_PANEL,
			foreground=cls.TEXT_PRIMARY,
			font=cls.FONT_NORMAL,
			focuscolor='none'
		)

		style.map(
			'TCheckbutton',
			background=[('active', cls.BG_PANEL)],
			foreground=[('active', cls.ACCENT_BLUE)]
		)

		style.configure(
			'Vertical.TScrollbar',
			background=cls.BG_PANEL,
			troughcolor=cls.BG_DARK,
			borderwidth=0,
			arrowsize=12
		)

		style.map(
			'Vertical.TScrollbar',
			background=[('active', cls.BORDER_COLOR), ('pressed', cls.BG_INPUT)]
		)
