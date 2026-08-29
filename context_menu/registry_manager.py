"""Registry scanning, mutation, disabling, backup, and restore manager."""

import ctypes
import datetime
import json
import os
import winreg
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass
class MenuItem:
	"""Represents a discovered Windows Explorer context menu action or handler."""

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
	extra_info: dict[str, Any] = field(default_factory=dict)


class RegistryManager:
	"""Interacts with Windows Registry to discover, toggle, delete, and add context menu items."""

	BLOCKED_SHELL_EXT_PATH: ClassVar[str] = (
		r'Software\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked'
	)

	CATEGORIES: ClassVar[dict[str, dict[str, Any]]] = {
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

	KNOWN_CLSIDS: ClassVar[dict[str, str]] = {
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

	def __init__(self) -> None:
		"""Initialize the manager and create the local backup directory."""
		self.backup_dir = os.path.join(os.getcwd(), 'backups')
		os.makedirs(self.backup_dir, exist_ok=True)

	@staticmethod
	def is_admin() -> bool:
		"""Check if the current process is running with administrative privileges."""
		try:
			return ctypes.windll.shell32.IsUserAnAdmin() != 0
		except (AttributeError, OSError):
			return False

	def get_blocked_clsids(self) -> set[str]:
		"""Get set of uppercase CLSID GUIDs blocked via Windows Shell Extensions blocklist."""
		blocked: set[str] = set()
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
			except OSError:
				pass

		return blocked

	def scan_category(self, category_key: str) -> list[MenuItem]:
		"""Scan a specific context menu category from both HKCU and HKLM."""
		items: list[MenuItem] = []
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
				self._scan_subkeys(
					root_name,
					root_hkey,
					full_path,
					category_key,
					item_type,
					blocked_clsids,
					items
				)

		return items

	def _scan_subkeys(
		self,
		root_name: str,
		root_hkey: int,
		full_path: str,
		category_key: str,
		item_type: str,
		blocked_clsids: set[str],
		out_items: list[MenuItem]
	) -> None:
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
						out_items.append(item)
		except OSError:
			pass

	def scan_all(self) -> dict[str, list[MenuItem]]:
		"""Scan all supported context menu categories."""
		results: dict[str, list[MenuItem]] = {}
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
		blocked_clsids: set[str]
	) -> MenuItem | None:
		try:
			with winreg.OpenKey(root_hkey, item_path, 0, winreg.KEY_READ) as key:
				num_subkeys, num_values, _ = winreg.QueryInfoKey(key)
				values_dict = self._read_key_values(key, num_values)

				name, icon = self._extract_display_info(key_name, values_dict)
				command = ''
				clsid = ''
				is_enabled = True

				if item_type == 'verb':
					is_enabled, command = self._parse_verb_item(
						root_name,
						root_hkey,
						item_path,
						values_dict
					)
				elif item_type == 'shellex':
					name, clsid, command, is_enabled = self._parse_shellex_item(
						key_name,
						values_dict,
						blocked_clsids
					)

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
		except OSError:
			return None

	@staticmethod
	def _read_key_values(key: winreg.HKEYType, num_values: int) -> dict[str, tuple[Any, int]]:
		values_dict: dict[str, tuple[Any, int]] = {}
		for i in range(num_values):
			try:
				v_name, v_data, v_type = winreg.EnumValue(key, i)
				values_dict[v_name] = (v_data, v_type)
			except OSError:
				pass

		return values_dict

	def _extract_display_info(
		self,
		key_name: str,
		values_dict: dict[str, tuple[Any, int]]
	) -> tuple[str, str]:
		name = key_name
		icon = ''

		if '' in values_dict:
			default_val = str(values_dict[''][0]).strip()
			if default_val:
				name = self._resolve_mui_string(default_val)

		if 'MUIVerb' in values_dict:
			mui_verb = str(values_dict['MUIVerb'][0]).strip()
			if mui_verb:
				name = self._resolve_mui_string(mui_verb)

		if 'Icon' in values_dict:
			icon = str(values_dict['Icon'][0])

		return name, icon

	def _parse_verb_item(
		self,
		root_name: str,
		root_hkey: int,
		item_path: str,
		values_dict: dict[str, tuple[Any, int]]
	) -> tuple[bool, str]:
		is_enabled = True
		command = ''

		if 'LegacyDisable' in values_dict or 'ProgrammaticAccessOnly' in values_dict:
			is_enabled = False

		if root_name == 'HKLM':
			try:
				with winreg.OpenKey(winreg.HKEY_CURRENT_USER, item_path, 0, winreg.KEY_READ) as hkcu_key:
					try:
						winreg.QueryValueEx(hkcu_key, 'LegacyDisable')
						is_enabled = False
					except OSError:
						pass
			except OSError:
				pass

		try:
			with winreg.OpenKey(root_hkey, f'{item_path}\\command', 0, winreg.KEY_READ) as cmd_key:
				cmd_val, _ = winreg.QueryValueEx(cmd_key, '')
				command = str(cmd_val)
		except OSError:
			pass

		return is_enabled, command

	@staticmethod
	def _extract_raw_clsid(key_name: str, values_dict: dict[str, tuple[Any, int]]) -> str:
		if '' in values_dict:
			raw_val = str(values_dict[''][0]).strip()
			if raw_val.startswith('{') and raw_val.endswith('}'):
				return raw_val

		if key_name.startswith('{') and key_name.endswith('}'):
			return key_name

		return ''

	def _parse_shellex_item(
		self,
		key_name: str,
		values_dict: dict[str, tuple[Any, int]],
		blocked_clsids: set[str]
	) -> tuple[str, str, str, bool]:
		clsid = self._extract_raw_clsid(key_name, values_dict)
		if not clsid:
			return key_name, '', 'COM Shell Extension', True

		is_enabled = clsid.upper() not in blocked_clsids
		friendly_name, dll_path, file_desc = self._resolve_clsid_info(clsid)
		name = self._format_shellex_name(key_name, clsid, friendly_name, file_desc)
		command = dll_path or clsid

		return name, clsid, command, is_enabled

	@staticmethod
	def _get_key_alias(key_name: str, clsid: str) -> str | None:
		clean_key = key_name.strip()
		if not clean_key or clean_key == clsid:
			return None

		return clean_key

	@classmethod
	def _format_shellex_name(
		cls,
		key_name: str,
		clsid: str,
		friendly_name: str | None,
		file_desc: str | None
	) -> str:
		alias = cls._get_key_alias(key_name, clsid)
		return cls._compose_shellex_label(clsid, friendly_name, file_desc, alias)

	@staticmethod
	def _compose_shellex_label(
		clsid: str,
		friendly_name: str | None,
		file_desc: str | None,
		alias: str | None
	) -> str:
		if friendly_name and file_desc and friendly_name != file_desc:
			return f'{friendly_name} [{file_desc}]'

		base_label = friendly_name or file_desc
		if base_label:
			if alias:
				return f'{base_label} ({alias})'

			return base_label

		if alias:
			return alias

		return f'Extension {clsid}'

	def _resolve_clsid_info(self, clsid: str) -> tuple[str | None, str | None, str | None]:
		clsid_lower = clsid.strip().lower()
		known_name = self.KNOWN_CLSIDS.get(clsid_lower)

		paths = [
			(winreg.HKEY_CLASSES_ROOT, f'CLSID\\{clsid}'),
			(winreg.HKEY_LOCAL_MACHINE, f'Software\\Classes\\CLSID\\{clsid}'),
			(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\CLSID\\{clsid}')
		]

		reg_name = self._find_clsid_name(paths)
		dll_path = self._find_clsid_dll(paths)
		file_desc = None
		if dll_path:
			file_desc = self._get_file_description(dll_path)

		friendly_name = known_name or reg_name
		return friendly_name, dll_path, file_desc

	@staticmethod
	def _find_clsid_name(paths: list[tuple[winreg.HKEYType, str]]) -> str | None:
		for root, path in paths:
			try:
				with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
					val, _ = winreg.QueryValueEx(key, '')
					if val and str(val).strip():
						return str(val).strip()
			except OSError:
				pass

		return None

	@staticmethod
	def _find_clsid_dll(paths: list[tuple[winreg.HKEYType, str]]) -> str | None:
		for root, path in paths:
			try:
				with winreg.OpenKey(root, f'{path}\\InprocServer32', 0, winreg.KEY_READ) as key:
					val, _ = winreg.QueryValueEx(key, '')
					if val and str(val).strip():
						return str(val).strip()
			except OSError:
				pass

		return None

	@classmethod
	def _get_file_description(cls, filepath: str) -> str | None:
		if not filepath or not os.path.exists(filepath):
			expanded_path = os.path.expandvars(filepath)
			if not os.path.exists(expanded_path):
				return None

			filepath = expanded_path

		try:
			size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
			if size == 0:
				return None

			res = ctypes.create_string_buffer(size)
			if ctypes.windll.version.GetFileVersionInfoW(filepath, 0, size, res) == 0:
				return None

			return cls._query_version_subblocks(res)
		except (AttributeError, OSError, ValueError):
			return None

	@staticmethod
	def _query_version_subblocks(res: Any) -> str | None:
		subblocks = [
			r'\StringFileInfo\040904b0\FileDescription',
			r'\StringFileInfo\000004b0\FileDescription',
			r'\StringFileInfo\040904e4\FileDescription',
			r'\StringFileInfo\040904b0\ProductName',
			r'\StringFileInfo\040904b0\CompanyName'
		]

		for subblock in subblocks:
			lp_buffer = ctypes.c_void_p()
			u_len = ctypes.c_uint()
			has_val = ctypes.windll.version.VerQueryValueW(
				res,
				subblock,
				ctypes.byref(lp_buffer),
				ctypes.byref(u_len)
			)

			if has_val and u_len.value > 0 and lp_buffer.value:
				val = ctypes.wstring_at(lp_buffer.value)
				if val and val.strip():
					return val.strip()

		return None

	@staticmethod
	def _resolve_mui_string(res_str: str) -> str:
		if not res_str.startswith('@'):
			return res_str

		try:
			buf = ctypes.create_unicode_buffer(1024)
			res = ctypes.windll.shlwapi.SHLoadIndirectString(
				ctypes.c_wchar_p(res_str),
				buf,
				ctypes.c_uint(1024),
				None
			)

			if res == 0 and buf.value:
				return buf.value.replace('&', '')
		except (AttributeError, OSError, ValueError):
			pass

		return res_str

	def set_item_enabled(self, item: MenuItem, enable: bool) -> tuple[bool, str]:
		"""Toggle context menu item between enabled and disabled."""
		if item.item_type == 'verb':
			return self._set_verb_enabled(item, enable)

		if item.item_type == 'shellex':
			return self._set_shellex_enabled(item, enable)

		return False, f'Unknown item type: {item.item_type}'

	def _determine_verb_target_root(self, item: MenuItem) -> winreg.HKEYType:
		if item.root_name == 'HKCU':
			return winreg.HKEY_CURRENT_USER

		if item.root_name == 'HKLM' and self.is_admin():
			return winreg.HKEY_LOCAL_MACHINE

		return winreg.HKEY_CURRENT_USER

	def _set_verb_enabled(self, item: MenuItem, enable: bool) -> tuple[bool, str]:
		target_root = self._determine_verb_target_root(item)

		try:
			with winreg.CreateKeyEx(target_root, item.key_path, 0, winreg.KEY_SET_VALUE) as key:
				if enable:
					try:
						winreg.DeleteValue(key, 'LegacyDisable')
					except OSError:
						pass

					try:
						winreg.DeleteValue(key, 'ProgrammaticAccessOnly')
					except OSError:
						pass
				else:
					winreg.SetValueEx(key, 'LegacyDisable', 0, winreg.REG_SZ, '')

			item.is_enabled = enable
			action_str = 'enabled' if enable else 'disabled'
			return True, f'Successfully {action_str} {item.name}'
		except PermissionError:
			return False, 'Permission denied. Please run the application as Administrator.'
		except OSError as e:
			return False, f'Failed to update verb item: {e}'

	def _set_shellex_enabled(self, item: MenuItem, enable: bool) -> tuple[bool, str]:
		clsid = item.clsid.strip()
		if not clsid:
			return False, 'Cannot toggle Shell Extension without a valid CLSID'

		try:
			with winreg.CreateKeyEx(
				winreg.HKEY_CURRENT_USER,
				self.BLOCKED_SHELL_EXT_PATH,
				0,
				winreg.KEY_SET_VALUE
			) as key:
				if enable:
					try:
						winreg.DeleteValue(key, clsid)
					except FileNotFoundError:
						pass
				else:
					winreg.SetValueEx(key, clsid, 0, winreg.REG_SZ, item.name)

			item.is_enabled = enable
			action_str = 'enabled' if enable else 'disabled'
			return True, f'Successfully {action_str} {item.name}'
		except OSError as e:
			return False, f'Failed to update shell extension status: {e}'

	def delete_item(self, item: MenuItem) -> tuple[bool, str]:
		"""Export backup and recursively delete context menu item from registry."""
		backup_ok, backup_path = self.backup_item(item)
		if not backup_ok:
			return False, f'Backup failed before deletion: {backup_path}'

		root_hkey = winreg.HKEY_CURRENT_USER
		if item.root_name == 'HKLM':
			if not self.is_admin():
				return False, 'Administrator privileges required to delete system (HKLM) context menu items.'

			root_hkey = winreg.HKEY_LOCAL_MACHINE

		try:
			self._delete_key_recursive(root_hkey, item.key_path)
			return True, f'Item deleted. Backup saved to: {backup_path}'
		except PermissionError:
			return False, 'Permission denied. Administrator privileges required.'
		except OSError as e:
			return False, f'Delete error: {e}'

	def backup_item(self, item: MenuItem) -> tuple[bool, str]:
		"""Export registry key values and subkeys to a JSON backup file."""
		root_hkey = winreg.HKEY_CURRENT_USER
		if item.root_name == 'HKLM':
			root_hkey = winreg.HKEY_LOCAL_MACHINE

		try:
			reg_dump = self._dump_key_recursive(root_hkey, item.key_path)
			safe_name = ''.join(c for c in item.name if c.isalnum() or c in ('_', '-')).strip()
			if not safe_name:
				safe_name = 'ContextItem'

			timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
			filename = f'backup_{safe_name}_{timestamp}.json'
			filepath = os.path.join(self.backup_dir, filename)

			payload = {
				'item': asdict(item),
				'registry_data': reg_dump,
				'exported_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
			}

			with open(filepath, 'w', encoding='utf-8') as f:
				json.dump(payload, f, indent=2)

			return True, filepath
		except OSError as e:
			return False, f'Backup error: {e}'

	def _dump_key_recursive(self, root_hkey: int, key_path: str) -> dict[str, Any]:
		data: dict[str, Any] = {'values': {}, 'subkeys': {}}
		try:
			with winreg.OpenKey(root_hkey, key_path, 0, winreg.KEY_READ) as key:
				num_subkeys, num_values, _ = winreg.QueryInfoKey(key)

				for i in range(num_values):
					try:
						v_name, v_data, v_type = winreg.EnumValue(key, i)
						data['values'][v_name] = {'data': v_data, 'type': v_type}
					except OSError:
						pass

				for i in range(num_subkeys):
					try:
						subkey_name = winreg.EnumKey(key, i)
						sub_path = f'{key_path}\\{subkey_name}'
						data['subkeys'][subkey_name] = self._dump_key_recursive(root_hkey, sub_path)
					except OSError:
						pass
		except OSError:
			pass

		return data

	def _delete_key_recursive(self, root_hkey: int, key_path: str) -> None:
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
		icon: str | None = None,
		position: str | None = None
	) -> tuple[bool, str]:
		"""Add a custom shell action verb to HKEY_CURRENT_USER."""
		target_map = {
			'files': r'Software\Classes\*\shell',
			'folders': r'Software\Classes\Directory\shell',
			'background': r'Software\Classes\Directory\Background\shell',
			'drives': r'Software\Classes\Drive\shell'
		}

		if category not in target_map:
			return False, f'Invalid category: {category}'

		safe_key_name = ''.join(c for c in name if c.isalnum() or c in ('_', '-')) or 'CustomAction'
		verb_path = f'{target_map[category]}\\{safe_key_name}'
		cmd_path = f'{verb_path}\\command'

		try:
			self._write_custom_verb_keys(verb_path, cmd_path, name, command, icon, position)
			return True, f'Successfully added "{name}" to {category}'
		except OSError as e:
			return False, f'Failed to add custom item: {e}'

	@staticmethod
	def _write_custom_verb_keys(
		verb_path: str,
		cmd_path: str,
		name: str,
		command: str,
		icon: str | None,
		position: str | None
	) -> None:
		with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, verb_path, 0, winreg.KEY_SET_VALUE) as verb_key:
			winreg.SetValueEx(verb_key, '', 0, winreg.REG_SZ, name)
			winreg.SetValueEx(verb_key, 'MUIVerb', 0, winreg.REG_SZ, name)

			if icon and icon.strip():
				winreg.SetValueEx(verb_key, 'Icon', 0, winreg.REG_SZ, icon.strip())

			if position in ('Top', 'Bottom'):
				winreg.SetValueEx(verb_key, 'Position', 0, winreg.REG_SZ, position)

		with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, cmd_path, 0, winreg.KEY_SET_VALUE) as cmd_key:
			winreg.SetValueEx(cmd_key, '', 0, winreg.REG_SZ, command.strip())
