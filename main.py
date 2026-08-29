"""Main entry point for Windows Context Menu Manager."""

import sys


def main() -> None:
	"""Launch the Windows Context Menu Manager desktop GUI."""
	if sys.platform != 'win32':
		print('Windows Context Menu Manager is only supported on Windows operating systems.')
		sys.exit(1)

	from context_menu.gui import ContextMenuApp

	app = ContextMenuApp()
	app.mainloop()


if __name__ == '__main__':
	main()
