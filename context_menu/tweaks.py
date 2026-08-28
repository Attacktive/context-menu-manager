import os
import sys
import subprocess
import winreg
import ctypes
from typing import Tuple

class SystemTweaks:
	WIN11_CLASSIC_CLSID = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'

	@classmethod
	def is_windows_11(cls) -> bool:
		try:
			return sys.getwindowsversion().build >= 22000
		except Exception:
			return False

	@classmethod
	def is_classic_menu_enabled(cls) -> bool:
		inproc_path = f'{cls.WIN11_CLASSIC_CLSID}\\InprocServer32'
		try:
			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, inproc_path, 0, winreg.KEY_READ) as key:
				val, _ = winreg.QueryValueEx(key, '')
				if val == '':
					return True
		except FileNotFoundError:
			return False
		except Exception:
			return False
		return False

	@classmethod
	def set_classic_menu_enabled(cls, enable: bool) -> Tuple[bool, str]:
		inproc_path = f'{cls.WIN11_CLASSIC_CLSID}\\InprocServer32'
		try:
			if enable:
				with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, inproc_path, 0, winreg.KEY_SET_VALUE) as key:
					winreg.SetValueEx(key, '', 0, winreg.REG_SZ, '')
				return True, 'Classic Windows 10 Context Menu enabled. Restart Explorer to apply.'
			else:
				try:
					winreg.DeleteKey(winreg.HKEY_CURRENT_USER, inproc_path)
				except FileNotFoundError:
					pass
				try:
					winreg.DeleteKey(winreg.HKEY_CURRENT_USER, cls.WIN11_CLASSIC_CLSID)
				except FileNotFoundError:
					pass
				return True, 'Windows 11 Modern Context Menu restored. Restart Explorer to apply.'
		except Exception as e:
			return False, f'Failed to update classic menu setting: {str(e)}'

	@classmethod
	def notify_shell_change(cls):
		try:
			# SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
			ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
		except Exception:
			pass

	@classmethod
	def restart_explorer(cls) -> Tuple[bool, str]:
		try:
			cls.notify_shell_change()
			subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], capture_output=True, check=False)
			# Start explorer detached
			subprocess.Popen(['explorer.exe'], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
			return True, 'Windows Explorer restarted successfully!'
		except Exception as e:
			return False, f'Failed to restart explorer: {str(e)}'

	@classmethod
	def open_in_regedit(cls, root_name: str, key_path: str) -> Tuple[bool, str]:
		regedit_lastkey_path = r'Software\Microsoft\Windows\CurrentVersion\Applets\Regedit'
		full_key = f'Computer\\HKEY_CURRENT_USER\\{key_path}'
		if root_name == 'HKLM':
			full_key = f'Computer\\HKEY_LOCAL_MACHINE\\{key_path}'

		try:
			with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, regedit_lastkey_path, 0, winreg.KEY_SET_VALUE) as key:
				winreg.SetValueEx(key, 'LastKey', 0, winreg.REG_SZ, full_key)

			subprocess.Popen(['regedit.exe', '/m'])
			return True, f'Opened RegEdit at {full_key}'
		except Exception as e:
			return False, f'Failed to open RegEdit: {str(e)}'

	@classmethod
	def relaunch_as_admin(cls):
		try:
			params = ' '.join([f'"{arg}"' for arg in sys.argv])
			ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
			sys.exit(0)
		except Exception:
			pass
