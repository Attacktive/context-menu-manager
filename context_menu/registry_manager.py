import os
import sys
import json
import winreg
import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any

@dataclass
class MenuItem:
	id: str
	name: str
	key_path: str
	root_name: str
	category: str
	item_type: str
	command: str = ''
	icon: str = ''
	clsid: str = ''
	is_enabled: bool = True
	is_user_level: bool = True
	sub_items_count: int = 0
	extra_info: Dict[str, Any] = field(default_factory=dict)

class RegistryManager:
	BLOCKED_SHELL_EXT_PATH = r'Software\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked'

	CATEGORIES = {
		'files': {
			'title': 'All Files (*)',
			'paths': [
				(r'*\shell', 'verb'),
				(r'*\shellex\ContextMenuHandlers', 'shellex'),
				(r'AllFilesystemObjects\shell', 'verb'),
				(r'AllFilesystemObjects\shellex\ContextMenuHandlers', 'shellex'),
			]
		},
		'folders': {
			'title': 'Folders & Directories',
			'paths': [
				(r'Directory\shell', 'verb'),
				(r'Directory\shellex\ContextMenuHandlers', 'shellex'),
				(r'Folder\shell', 'verb'),
				(r'Folder\shellex\ContextMenuHandlers', 'shellex'),
			]
		},
		'background': {
			'title': 'Desktop & Folder Background',
			'paths': [
				(r'Directory\Background\shell', 'verb'),
				(r'Directory\Background\shellex\ContextMenuHandlers', 'shellex'),
				(r'DesktopBackground\shell', 'verb'),
				(r'DesktopBackground\shellex\ContextMenuHandlers', 'shellex'),
			]
		},
		'drives': {
			'title': 'Drives',
			'paths': [
				(r'Drive\shell', 'verb'),
				(r'Drive\shellex\ContextMenuHandlers', 'shellex'),
			]
		}
	}

	def __init__(self):
		self.backup_dir = os.path.join(os.getcwd(), 'backups')
		os.makedirs(self.backup_dir, exist_ok=True)

	def is_admin(self) -> bool:
		try:
			import ctypes
			return ctypes.windll.shell32.IsUserAnAdmin() != 0
		except Exception:
			return False

	def get_blocked_clsids(self) -> set:
		blocked = set()
		roots = [
			(winreg.HKEY_CURRENT_USER, self.BLOCKED_SHELL_EXT_PATH),
			(winreg.HKEY_LOCAL_MACHINE, self.BLOCKED_SHELL_EXT_PATH)
		]

		for root, path in roots:
			try:
				with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
					num_values = winreg.QueryInfoKey(key)[1]
					for i in range(num_values):
						val_name, _, _ = winreg.EnumValue(key, i)
						if val_name:
							blocked.add(val_name.strip().upper())
			except FileNotFoundError:
				pass
			except Exception:
				pass

		return blocked

	def scan_category(self, category_key: str) -> List[MenuItem]:
		items: List[MenuItem] = []
		if category_key not in self.CATEGORIES:
			return items

		blocked_clsids = self.get_blocked_clsids()
		config = self.CATEGORIES[category_key]

		roots = [
			('HKCU', winreg.HKEY_CURRENT_USER, r'Software\Classes'),
			('HKLM', winreg.HKEY_LOCAL_MACHINE, r'Software\Classes')
		]

		for path_suffix, item_type in config['paths']:
			for root_name, root_hkey, base_classes in roots:
				full_path = f'{base_classes}\\{path_suffix}'
				try:
					with winreg.OpenKey(root_hkey, full_path, 0, winreg.KEY_READ) as parent_key:
						num_subkeys = winreg.QueryInfoKey(parent_key)[0]
						for i in range(num_subkeys):
							subkey_name = winreg.EnumKey(parent_key, i)
							item_path = f'{full_path}\\{subkey_name}'
							item = self._parse_item(
								root_name=root_name,
								root_hkey=root_hkey,
								item_path=item_path,
								key_name=subkey_name,
								category=category_key,
								item_type=item_type,
								blocked_clsids=blocked_clsids
							)

							if item is not None:
								items.append(item)
				except FileNotFoundError:
					pass
				except PermissionError:
					pass
				except Exception:
					pass

		return items

	def scan_all(self) -> Dict[str, List[MenuItem]]:
		results = {}
		for cat in self.CATEGORIES:
			results[cat] = self.scan_category(cat)
		return results

	def _parse_item(
		self,
		root_name: str,
		root_hkey: int,
		item_path: str,
		key_name: str,
		category: str,
		item_type: str,
		blocked_clsids: set
	) -> Optional[MenuItem]:
		try:
			with winreg.OpenKey(root_hkey, item_path, 0, winreg.KEY_READ) as key:
				num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

				values_dict = {}
				for i in range(num_values):
					try:
						v_name, v_data, v_type = winreg.EnumValue(key, i)
						values_dict[v_name] = (v_data, v_type)
					except Exception:
						pass

				name = key_name
				command = ''
				icon = ''
				clsid = ''
				is_enabled = True

				if '' in values_dict:
					default_val = str(values_dict[''][0])
					if default_val.strip():
						name = self._resolve_mui_string(default_val.strip())

				if 'MUIVerb' in values_dict:
					mui_verb = str(values_dict['MUIVerb'][0])
					if mui_verb.strip():
						name = self._resolve_mui_string(mui_verb.strip())
				if 'Icon' in values_dict:
					icon = str(values_dict['Icon'][0])

				if item_type == 'verb':
					if 'LegacyDisable' in values_dict or 'ProgrammaticAccessOnly' in values_dict:
						is_enabled = False

					# Check user-level shadow disable if this is HKLM
					if root_name == 'HKLM':
						hkcu_mirror = item_path
						try:
							with winreg.OpenKey(winreg.HKEY_CURRENT_USER, hkcu_mirror, 0, winreg.KEY_READ) as hkcu_key:
								try:
									winreg.QueryValueEx(hkcu_key, 'LegacyDisable')
									is_enabled = False
								except FileNotFoundError:
									pass
						except FileNotFoundError:
							pass

					try:
						with winreg.OpenKey(root_hkey, f'{item_path}\\command', 0, winreg.KEY_READ) as cmd_key:
							cmd_val, _ = winreg.QueryValueEx(cmd_key, '')
							command = str(cmd_val)
					except Exception:
						pass

				elif item_type == 'shellex':
					# For ShellEx, the default value or key name is often a CLSID GUID
					if '' in values_dict:
						raw_clsid = str(values_dict[''][0]).strip()
						if raw_clsid.startswith('{') and raw_clsid.endswith('}'):
							clsid = raw_clsid
					if not clsid and key_name.startswith('{') and key_name.endswith('}'):
						clsid = key_name

					if clsid:
						clsid_upper = clsid.upper()
						if clsid_upper in blocked_clsids:
							is_enabled = False

						friendly_name, dll_path, file_desc = self._resolve_clsid_info(clsid)

						# Construct the clearest human-readable name
						clean_key = key_name.strip()
						if friendly_name and file_desc and friendly_name != file_desc:
							name = f'{friendly_name} [{file_desc}]'
						elif friendly_name:
							if clean_key and clean_key != clsid:
								name = f'{friendly_name} ({clean_key})'
							else:
								name = friendly_name
						elif file_desc:
							if clean_key and clean_key != clsid:
								name = f'{file_desc} ({clean_key})'
							else:
								name = file_desc
						elif clean_key and clean_key != clsid:
							name = clean_key
						else:
							name = f'Extension {clsid}'

						if dll_path:
							command = dll_path
						else:
							command = clsid
					else:
						command = 'COM Shell Extension'

				item_id = f'{root_name}:{item_path}'
				return MenuItem(
					id=item_id,
					name=name,
					key_path=item_path,
					root_name=root_name,
					category=category,
					item_type=item_type,
					command=command,
					icon=icon,
					clsid=clsid,
					is_enabled=is_enabled,
					is_user_level=(root_name == 'HKCU'),
					sub_items_count=num_subkeys,
					extra_info={'key_name': key_name, 'values': {k: str(v[0]) for k, v in values_dict.items()}}
				)
		except Exception:
			return None

	KNOWN_CLSIDS = {
		'{f81e9010-6ea4-11ce-a7ff-00aa003ca9f6}': 'Give access to / Sharing',
		'{f81e9010-6ea4-11ce-a316-00aa00369c81}': 'Give access to / Sharing',
		'{09a47860-11b0-4da5-afa5-26d86198a780}': 'Microsoft Defender Antivirus',
		'{a2a9545d-a0c2-42b4-9708-a0b2badd77c8}': 'Pin to Start',
		'{90aa3a4e-1cba-4233-b8bb-535773d48449}': 'Pin to Taskbar',
		'{7ba4c740-9e81-11cf-99d3-00aa004ae837}': 'Send to Menu',
		'{09799afb-ad67-11d1-abcd-00c04fc30936}': 'Open with Menu',
		'{f3d06e7c-1e45-4a26-847e-f9fcdee59be0}': 'Copy as Path',
		'{d969a300-e7ff-11d0-a93b-00a0c90f2719}': 'New Item Menu',
		'{3d1975af-48c6-4f8e-a182-be0e08fa86a9}': 'NVIDIA Control Panel',
		'{f2e8b4a1-9c7d-4f6e-b3a5-8d2c1f4e9b7a}': 'NVIDIA App Desktop Context',
		'{cb3d0f55-bc2c-4c1a-85ed-23ed75b5106b}': 'OneDrive File Sync',
		'{e61bf828-5e63-4287-bef1-60b1a4fde0e3}': 'Work Folders',
		'{470c0ebd-5d73-4d58-9ced-e91e22e23282}': 'Pin to Start Screen',
		'{596ab062-b4d2-4215-9f74-e9109b0a8153}': 'Restore Previous Versions',
	}

	def _resolve_clsid_info(self, clsid: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
		clsid_lower = clsid.strip().lower()
		known_name = self.KNOWN_CLSIDS.get(clsid_lower)

		paths = [
			(winreg.HKEY_CLASSES_ROOT, f'CLSID\\{clsid}'),
			(winreg.HKEY_LOCAL_MACHINE, f'Software\\Classes\\CLSID\\{clsid}'),
			(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\CLSID\\{clsid}')
		]

		reg_name = None
		dll_path = None

		for root, path in paths:
			if not reg_name:
				try:
					with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
						val, _ = winreg.QueryValueEx(key, '')
						if val and str(val).strip():
							reg_name = str(val).strip()
				except Exception:
					pass

			if not dll_path:
				try:
					with winreg.OpenKey(root, f'{path}\\InprocServer32', 0, winreg.KEY_READ) as key:
						val, _ = winreg.QueryValueEx(key, '')
						if val and str(val).strip():
							dll_path = str(val).strip()
				except Exception:
					pass

			if reg_name and dll_path:
				break

		file_desc = None
		if dll_path:
			file_desc = self._get_file_description(dll_path)

		friendly_name = known_name or reg_name
		return friendly_name, dll_path, file_desc

	def _get_file_description(self, filepath: str) -> Optional[str]:
		if not filepath:
			return None

		expanded_path = os.path.expandvars(filepath)
		if not os.path.exists(expanded_path):
			return None

		try:
			import ctypes
			size = ctypes.windll.version.GetFileVersionInfoSizeW(expanded_path, None)
			if size == 0:
				return None

			res = ctypes.create_string_buffer(size)
			if not ctypes.windll.version.GetFileVersionInfoW(expanded_path, 0, size, res):
				return None

			u_len = ctypes.c_uint()
			subblocks = [
				r'\StringFileInfo\040904b0\FileDescription',
				r'\StringFileInfo\040904E4\FileDescription',
				r'\StringFileInfo\000004b0\FileDescription',
				r'\StringFileInfo\040904b0\ProductName',
				r'\StringFileInfo\040904b0\CompanyName'
			]

			for subblock in subblocks:
				lp_buffer = ctypes.c_void_p()
				has_val = ctypes.windll.version.VerQueryValueW(
					res,
					subblock,
					ctypes.byref(lp_buffer),
					ctypes.byref(u_len)
				)

				if has_val:
					if u_len.value > 0 and lp_buffer.value:
						val = ctypes.wstring_at(lp_buffer.value)
						if val and val.strip():
							return val.strip()
		except Exception:
			pass
		return None

	def _resolve_mui_string(self, res_str: str) -> str:
		if not res_str.startswith('@'):
			return res_str
		try:
			import ctypes
			buf = ctypes.create_unicode_buffer(1024)
			res = ctypes.windll.shlwapi.SHLoadIndirectString(
				ctypes.c_wchar_p(res_str),
				buf,
				ctypes.c_uint(1024),
				None
			)

			if res == 0 and buf.value:
				# Clean up Windows UI accelerators like '&Open' -> 'Open'
				return buf.value.replace('&', '')
		except Exception:
			pass
		return res_str

	def set_item_enabled(self, item: MenuItem, enable: bool) -> Tuple[bool, str]:
		if item.item_type == 'verb':
			return self._set_verb_enabled(item, enable)
		elif item.item_type == 'shellex':
			return self._set_shellex_enabled(item, enable)
		return False, 'Unknown item type'

	def _set_verb_enabled(self, item: MenuItem, enable: bool) -> Tuple[bool, str]:
		target_root = winreg.HKEY_LOCAL_MACHINE
		if item.root_name == 'HKCU':
			target_root = winreg.HKEY_CURRENT_USER

		target_path = item.key_path

		# If trying to modify HKLM without admin rights, write to HKCU mirror
		if item.root_name == 'HKLM' and not self.is_admin():
			target_root = winreg.HKEY_CURRENT_USER

		try:
			# Ensure key exists in target
			try:
				key = winreg.OpenKey(target_root, target_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
			except FileNotFoundError:
				key = winreg.CreateKeyEx(target_root, target_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)

			with key:
				if enable:
					try:
						winreg.DeleteValue(key, 'LegacyDisable')
					except FileNotFoundError:
						pass
					try:
						winreg.DeleteValue(key, 'ProgrammaticAccessOnly')
					except FileNotFoundError:
						pass
				else:
					winreg.SetValueEx(key, 'LegacyDisable', 0, winreg.REG_SZ, '')

			item.is_enabled = enable
			action_text = 'enabled'
			if not enable:
				action_text = 'disabled'

			return True, f'Successfully {action_text} {item.name}'
		except PermissionError:
			return False, 'Permission denied. Please run the application as Administrator.'
		except Exception as e:
			return False, f'Error: {str(e)}'

	def _set_shellex_enabled(self, item: MenuItem, enable: bool) -> Tuple[bool, str]:
		if not item.clsid:
			return False, 'Cannot toggle Shell Extension without a valid CLSID'

		clsid = item.clsid.strip()
		blocked_path = self.BLOCKED_SHELL_EXT_PATH

		try:
			# Try HKCU first as it doesn't need admin privileges
			try:
				key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, blocked_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
			except FileNotFoundError:
				key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, blocked_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)

			with key:
				if enable:
					try:
						winreg.DeleteValue(key, clsid)
					except FileNotFoundError:
						pass
					# If running as admin, also clear from HKLM
					if self.is_admin():
						try:
							with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, blocked_path, 0, winreg.KEY_SET_VALUE) as hklm_key:
								try:
									winreg.DeleteValue(hklm_key, clsid)
								except FileNotFoundError:
									pass
						except Exception:
							pass
				else:
					winreg.SetValueEx(key, clsid, 0, winreg.REG_SZ, item.name)

			item.is_enabled = enable
			action_text = 'enabled'
			if not enable:
				action_text = 'disabled'

			return True, f'Successfully {action_text} {item.name}'
		except PermissionError:
			return False, 'Permission denied. Please run as Administrator.'
		except Exception as e:
			return False, f'Error: {str(e)}'

	def backup_item(self, item: MenuItem) -> Tuple[bool, str]:
		timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
		safe_chars = []
		for c in item.name:
			if c.isalnum() or c in ('-', '_'):
				safe_chars.append(c)
			else:
				safe_chars.append('_')
		safe_name = ''.join(safe_chars)
		filename = f'backup_{safe_name}_{timestamp}.json'
		filepath = os.path.join(self.backup_dir, filename)

		root_hkey = winreg.HKEY_LOCAL_MACHINE
		if item.root_name == 'HKCU':
			root_hkey = winreg.HKEY_CURRENT_USER

		try:
			key_data = self._export_key_recursive(root_hkey, item.key_path)
			payload = {
				'item': asdict(item),
				'registry_data': key_data,
				'exported_at': datetime.datetime.now().isoformat()
			}
			with open(filepath, 'w', encoding='utf-8') as f:
				json.dump(payload, f, indent='\t', ensure_ascii=False)
			return True, filepath
		except Exception as e:
			return False, f'Backup failed: {str(e)}'

	def _export_key_recursive(self, root_hkey: int, key_path: str) -> Dict[str, Any]:
		result = {'values': {}, 'subkeys': {}}
		try:
			with winreg.OpenKey(root_hkey, key_path, 0, winreg.KEY_READ) as key:
				num_subkeys, num_values, _ = winreg.QueryInfoKey(key)
				for i in range(num_values):
					try:
						v_name, v_data, v_type = winreg.EnumValue(key, i)
						result['values'][v_name] = {'data': v_data, 'type': v_type}
					except Exception:
						pass

				for i in range(num_subkeys):
					try:
						subkey_name = winreg.EnumKey(key, i)
						sub_path = f'{key_path}\\{subkey_name}'
						result['subkeys'][subkey_name] = self._export_key_recursive(root_hkey, sub_path)
					except Exception:
						pass
		except Exception:
			pass
		return result

	def delete_item(self, item: MenuItem) -> Tuple[bool, str]:
		# Always backup first
		backup_ok, backup_path = self.backup_item(item)
		if not backup_ok:
			return False, f'Deletion aborted: Could not create backup ({backup_path})'

		root_hkey = winreg.HKEY_LOCAL_MACHINE
		if item.root_name == 'HKCU':
			root_hkey = winreg.HKEY_CURRENT_USER
		try:
			self._delete_key_recursive(root_hkey, item.key_path)
			return True, f'Item deleted. Backup saved to: {backup_path}'
		except PermissionError:
			return False, 'Permission denied. Administrator privileges required to delete system keys.'
		except Exception as e:
			return False, f'Delete error: {str(e)}'

	def _delete_key_recursive(self, root_hkey: int, key_path: str):
		with winreg.OpenKey(root_hkey, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
			while True:
				try:
					subkey = winreg.EnumKey(key, 0)
					self._delete_key_recursive(root_hkey, f'{key_path}\\{subkey}')
				except OSError:
					break
		winreg.DeleteKey(root_hkey, key_path)

	def add_custom_item(
		self,
		category: str,
		name: str,
		command: str,
		icon: Optional[str] = None,
		position: Optional[str] = None
	) -> Tuple[bool, str]:
		target_map = {
			'files': r'Software\Classes\*\shell',
			'folders': r'Software\Classes\Directory\shell',
			'background': r'Software\Classes\Directory\Background\shell',
			'drives': r'Software\Classes\Drive\shell'
		}

		if category not in target_map:
			return False, f'Invalid category: {category}'

		safe_key_name = ''.join(c for c in name if c.isalnum() or c in ('_', '-'))
		if not safe_key_name:
			safe_key_name = 'CustomAction'

		verb_path = f'{target_map[category]}\\{safe_key_name}'
		cmd_path = f'{verb_path}\\command'

		try:
			with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, verb_path, 0, winreg.KEY_SET_VALUE) as verb_key:
				winreg.SetValueEx(verb_key, '', 0, winreg.REG_SZ, name)
				winreg.SetValueEx(verb_key, 'MUIVerb', 0, winreg.REG_SZ, name)

				if icon and icon.strip():
					winreg.SetValueEx(verb_key, 'Icon', 0, winreg.REG_SZ, icon.strip())

				if position in ('Top', 'Bottom'):
					winreg.SetValueEx(verb_key, 'Position', 0, winreg.REG_SZ, position)

			with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, cmd_path, 0, winreg.KEY_SET_VALUE) as cmd_key:
				winreg.SetValueEx(cmd_key, '', 0, winreg.REG_SZ, command.strip())

			return True, f'Successfully added "{name}" to {category}'
		except Exception as e:
			return False, f'Failed to add custom item: {str(e)}'
