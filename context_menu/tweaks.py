"""Windows system tweaks and Explorer integration helpers."""

import ctypes
import os
import subprocess  # nosec B404
import sys
import time
import winreg
from typing import ClassVar


class SystemTweaks:
	"""Helpers for Windows 11 context menu tweaks, registry navigation, and Explorer control."""

	WIN11_CLASSIC_CLSID: ClassVar[str] = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'

	@classmethod
	def is_windows_11(cls) -> bool:
		"""Check if the current operating system is Windows 11 (build >= 22000)."""
		try:
			return sys.getwindowsversion().build >= 22000
		except (AttributeError, OSError):
			return False

	@classmethod
	def is_classic_menu_enabled(cls) -> bool:
		"""Check if the classic Windows 10 context menu override is active in the registry."""
		inproc_path = f'{cls.WIN11_CLASSIC_CLSID}\\InprocServer32'

		try:
			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, inproc_path, 0, winreg.KEY_READ) as key:
				val, _ = winreg.QueryValueEx(key, '')
				if val == '':
					return True
		except OSError:
			return False

		return False

	@classmethod
	def set_classic_menu_enabled(cls, enable: bool) -> tuple[bool, str]:
		"""Enable or disable the classic Windows 10 context menu on Windows 11."""
		inproc_path = f'{cls.WIN11_CLASSIC_CLSID}\\InprocServer32'

		try:
			if enable:
				with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, inproc_path, 0, winreg.KEY_SET_VALUE) as key:
					winreg.SetValueEx(key, '', 0, winreg.REG_SZ, '')

				return True, 'Classic Windows 10 Context Menu enabled. Restart Explorer to apply.'

			try:
				winreg.DeleteKey(winreg.HKEY_CURRENT_USER, inproc_path)
			except FileNotFoundError:
				pass

			try:
				winreg.DeleteKey(winreg.HKEY_CURRENT_USER, cls.WIN11_CLASSIC_CLSID)
			except FileNotFoundError:
				pass

			return True, 'Windows 11 Modern Context Menu restored. Restart Explorer to apply.'
		except OSError as e:
			return False, f'Failed to update classic menu setting: {e}'

	@classmethod
	def notify_shell_change(cls) -> None:
		"""Notify the shell that associations and context menu extensions changed."""
		try:
			# SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_FLUSH = 0x1000
			ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x1000, None, None)
		except OSError:
			pass

	@classmethod
	def restart_explorer(cls) -> tuple[bool, str]:
		"""Restart the Windows Explorer shell process cleanly."""
		try:
			cls.notify_shell_change()

			subprocess.run(  # nosec B603
				[r'C:\Windows\System32\taskkill.exe', '/f', '/im', 'explorer.exe'],
				capture_output=True,
				check=False
			)

			time.sleep(0.5)

			res = ctypes.windll.shell32.ShellExecuteW(None, 'open', r'C:\Windows\explorer.exe', None, None, 1)
			if res <= 32:
				os.startfile(r'C:\Windows\explorer.exe')  # nosec B606

			return True, 'Windows Explorer restarted successfully!'
		except OSError as e:
			return False, f'Failed to restart explorer: {e}'

	@classmethod
	def open_in_regedit(cls, root_name: str, key_path: str) -> tuple[bool, str]:
		"""Open the Windows Registry Editor navigated directly to the specified key."""
		regedit_lastkey_path = r'Software\Microsoft\Windows\CurrentVersion\Applets\Regedit'
		full_key = f'Computer\\HKEY_CURRENT_USER\\{key_path}'
		if root_name == 'HKLM':
			full_key = f'Computer\\HKEY_LOCAL_MACHINE\\{key_path}'

		try:
			with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, regedit_lastkey_path, 0, winreg.KEY_SET_VALUE) as key:
				winreg.SetValueEx(key, 'LastKey', 0, winreg.REG_SZ, full_key)

			subprocess.Popen([r'C:\Windows\regedit.exe', '/m'])  # nosec B603

			return True, f'Opened RegEdit at {full_key}'
		except OSError as e:
			return False, f'Failed to open RegEdit: {e}'

	@classmethod
	def relaunch_as_admin(cls) -> None:
		"""Relaunch the current application with elevated administrator privileges."""
		try:
			params = ' '.join([f'"{arg}"' for arg in sys.argv])
			ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
			sys.exit(0)
		except OSError:
			pass
