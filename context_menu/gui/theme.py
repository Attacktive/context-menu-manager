import tkinter as tk
from tkinter import ttk

class Theme:
	# Modern Fluent / Slate Dark Palette
	BG_DARK = '#181825'
	BG_PANEL = '#1e1e2e'
	BG_CARD = '#252538'
	BG_INPUT = '#313244'
	BORDER_COLOR = '#45475a'

	TEXT_PRIMARY = '#cdd6f4'
	TEXT_MUTED = '#a6adc8'
	TEXT_DISABLED = '#6c7086'

	ACCENT_BLUE = '#89b4fa'
	ACCENT_HOVER = '#b4befe'
	ACCENT_GREEN = '#a6e3a1'
	ACCENT_RED = '#f38ba8'
	ACCENT_ORANGE = '#fab387'
	ACCENT_PURPLE = '#cba6f7'

	FONT_FAMILY = 'Segoe UI'
	FONT_TITLE = (FONT_FAMILY, 14, 'bold')
	FONT_SUBTITLE = (FONT_FAMILY, 10, 'normal')
	FONT_HEADER = (FONT_FAMILY, 11, 'bold')
	FONT_NORMAL = (FONT_FAMILY, 10, 'normal')
	FONT_BOLD = (FONT_FAMILY, 10, 'bold')
	FONT_SMALL = (FONT_FAMILY, 9, 'normal')
	FONT_CODE = ('Consolas', 9, 'normal')

	@classmethod
	def apply(cls, root: tk.Tk):
		root.configure(bg=cls.BG_DARK)

		style = ttk.Style(root)
		try:
			style.theme_use('clam')
		except Exception:
			pass

		# Base Frame
		style.configure('TFrame', background=cls.BG_DARK)
		style.configure('Card.TFrame', background=cls.BG_PANEL, relief='flat')
		style.configure('Border.TFrame', background=cls.BORDER_COLOR)

		# Label
		style.configure('TLabel', background=cls.BG_DARK, foreground=cls.TEXT_PRIMARY, font=cls.FONT_NORMAL)
		style.configure('Card.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_PRIMARY, font=cls.FONT_NORMAL)
		style.configure('Muted.TLabel', background=cls.BG_DARK, foreground=cls.TEXT_MUTED, font=cls.FONT_SMALL)
		style.configure('CardMuted.TLabel', background=cls.BG_PANEL, foreground=cls.TEXT_MUTED, font=cls.FONT_SMALL)
		style.configure('Title.TLabel', background=cls.BG_DARK, foreground=cls.TEXT_PRIMARY, font=cls.FONT_TITLE)
		style.configure('Header.TLabel', background=cls.BG_PANEL, foreground=cls.ACCENT_BLUE, font=cls.FONT_HEADER)

		# Buttons
		style.configure(
			'TButton',
			background=cls.BG_INPUT,
			foreground=cls.TEXT_PRIMARY,
			font=cls.FONT_BOLD,
			borderwidth=0,
			focuscolor='none',
			padding=(10, 6)
		)

		style.map(
			'TButton',
			background=[('active', cls.BORDER_COLOR), ('pressed', cls.BG_CARD), ('disabled', cls.BG_PANEL)],
			foreground=[('disabled', cls.TEXT_DISABLED)]
		)

		# Primary Accent Button
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
			background=[('active', cls.ACCENT_HOVER), ('pressed', '#74c7ec'), ('disabled', cls.BG_INPUT)],
			foreground=[('disabled', cls.TEXT_DISABLED)]
		)

		# Danger Red Button
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
			background=[('active', '#eba0ac'), ('pressed', '#f38ba8'), ('disabled', cls.BG_INPUT)],
			foreground=[('disabled', cls.TEXT_DISABLED)]
		)

		# Success Green Button
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
			background=[('active', '#94e2d5'), ('pressed', '#a6e3a1'), ('disabled', cls.BG_INPUT)],
			foreground=[('disabled', cls.TEXT_DISABLED)]
		)

		# Notebook (Tabs)
		style.configure(
			'TNotebook',
			background=cls.BG_DARK,
			borderwidth=0,
			tabmargins=[4, 4, 4, 0]
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
			background=[('selected', cls.BG_CARD), ('active', cls.BG_INPUT)],
			foreground=[('selected', cls.ACCENT_BLUE), ('active', cls.TEXT_PRIMARY)],
			expand=[('selected', [0, 2, 0, 0])]
		)

		# Treeview (Items List)
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
			borderwidth=0,
			padding=(8, 6)
		)

		style.map(
			'Treeview',
			background=[('selected', cls.BG_INPUT)],
			foreground=[('selected', cls.ACCENT_BLUE)]
		)

		style.map(
			'Treeview.Heading',
			background=[('active', cls.BORDER_COLOR)]
		)

		# Entry
		style.configure(
			'TEntry',
			fieldbackground=cls.BG_INPUT,
			foreground=cls.TEXT_PRIMARY,
			insertcolor=cls.TEXT_PRIMARY,
			borderwidth=0,
			padding=(8, 6)
		)

		# Checkbutton
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

		# Scrollbar
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
