import struct
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import capstone
except ImportError:
    capstone = None

logger = logging.getLogger("binary-parser")


class BinaryParser:
    _instance_cache = {}

    def __init__(self, file_path: str):
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        self.file_path = file_path
        self.file_handle = open(file_path, 'rb')
        self._elf_header = self._parse_elf_header()
        self.is_64bit = self._elf_header['is_64bit']
        self._endian = self._elf_header['endian']
        self._sections = self._parse_section_headers()
        self._resolve_section_names()
        self._dynamic_info = self._parse_dynamic_section()
        self._symbols = self._parse_symbol_table()
        self.relocations = self._parse_relocations()
        self.reloc_map = {rel['got_address']: rel['symbol'] for rel in self.relocations}

    def __del__(self):
        if hasattr(self, 'file_handle') and self.file_handle and not self.file_handle.closed:
            self.file_handle.close()

    @staticmethod
    def _get_parser_instance(file_path: str) -> 'BinaryParser':
        if file_path not in BinaryParser._instance_cache:
            BinaryParser._instance_cache[file_path] = BinaryParser(file_path)
        return BinaryParser._instance_cache[file_path]

    @classmethod
    def clear_cache(cls):
        for parser in cls._instance_cache.values():
            del parser
        cls._instance_cache.clear()

    def _read_struct(self, offset: int, fmt: str) -> tuple:
        size = struct.calcsize(fmt)
        self.file_handle.seek(offset)
        buffer = self.file_handle.read(size)
        if len(buffer) < size:
            raise IOError("Read past end of file while parsing struct.")
        return struct.unpack(self._endian + fmt, buffer)

    def _read_string(self, offset: int) -> str:
        self.file_handle.seek(offset)
        chars = []
        while True:
            char = self.file_handle.read(1)
            if char == b'\x00' or not char: break
            chars.append(char)
        return b''.join(chars).decode('latin-1')

    def _parse_elf_header(self) -> Dict[str, Any]:
        magic = self._read_struct(0, '4s')[0]
        if magic != b'\x7fELF': raise ValueError("Not a valid ELF file.")
        ei_class, ei_data = self._read_struct(4, 'BB')[:2]
        is_64bit = (ei_class == 2)
        endian = '<' if ei_data == 1 else '>'
        fmt = 'HHIQQQIHHHHHH' if is_64bit else 'HHIHHIIIIII'
        _, _, _, _, _, e_shoff, _, _, _, _, e_shentsize, e_shnum, e_shstrndx = self._read_struct(18, fmt)
        return {"is_64bit": is_64bit, "endian": endian, "e_shoff": e_shoff,
                "e_shentsize": e_shentsize, "e_shnum": e_shnum, "e_shstrndx": e_shstrndx}

    def _parse_section_headers(self) -> Dict[int, Dict[str, Any]]:
        sections = {}
        shoff, shentsize, shnum = self._elf_header['e_shoff'], self._elf_header['e_shentsize'], self._elf_header[
            'e_shnum']
        fmt = 'IIQQQQIIQQ' if self.is_64bit else 'IIIIIIIIII'
        for i in range(shnum):
            offset = shoff + i * shentsize
            sh_name, _, _, sh_addr, sh_offset, sh_size, _, _, _, sh_entsize = self._read_struct(offset, fmt)
            sections[i] = {'name_offset': sh_name, 'name': '', 'addr': sh_addr, 'offset': sh_offset, 'size': sh_size,
                           'entsize': sh_entsize}
        return sections

    def _resolve_section_names(self):
        shstrndx = self._elf_header['e_shstrndx']
        if shstrndx >= self._elf_header['e_shnum']: return
        string_table_offset = self._sections[shstrndx]['offset']
        for i in self._sections:
            self._sections[i]['name'] = self._read_string(string_table_offset + self._sections[i]['name_offset'])

    def get_section(self, name: str) -> Optional[Dict[str, Any]]:
        return next((sec for sec in self._sections.values() if sec['name'] == name), None)

    def _parse_dynamic_section(self) -> Dict[int, int]:
        sec = self.get_section('.dynamic')
        if not sec: return {}
        dyn_info = {}
        fmt = 'Qq' if self.is_64bit else 'Ii'
        for i in range(sec['size'] // sec['entsize']):
            d_tag, d_val = self._read_struct(sec['offset'] + i * sec['entsize'], fmt)
            if d_tag == 0: break
            dyn_info[d_tag] = d_val
        return dyn_info

    def _parse_symbol_table(self) -> Dict[int, Dict[str, Any]]:
        symtab_addr, strtab_addr, syment_size = self._dynamic_info.get(6), self._dynamic_info.get(
            5), self._dynamic_info.get(11)
        if not all((symtab_addr, strtab_addr, syment_size)): return {}
        dynsym_sec = next((s for s in self._sections.values() if s['addr'] == symtab_addr), None)
        dynstr_sec = next((s for s in self._sections.values() if s['addr'] == strtab_addr), None)
        if not dynsym_sec or not dynstr_sec: return {}
        symbols = {}
        fmt = 'IBBHQQ' if self.is_64bit else 'IIIBBH'
        for i in range(dynsym_sec['size'] // syment_size):
            st_name_idx, *_ = self._read_struct(dynsym_sec['offset'] + i * syment_size, fmt)
            symbols[i] = {'name': self._read_string(dynstr_sec['offset'] + st_name_idx).split('@')[0]}
        return symbols

    def _parse_relocations(self) -> List[Dict[str, Any]]:
        rel_addr = self._dynamic_info.get(23)
        if not rel_addr: return []
        rel_sec = next((s for s in self._sections.values() if s['addr'] == rel_addr), None)
        if not rel_sec: return []
        relocations = []
        entsize = 24 if self.is_64bit else 12
        fmt = 'QQQ' if self.is_64bit else 'III'
        for i in range(rel_sec['size'] // entsize):
            r_offset, r_info, _ = self._read_struct(rel_sec['offset'] + i * entsize, fmt)
            sym_idx = r_info >> 32 if self.is_64bit else r_info >> 8
            symbol = self._symbols.get(sym_idx, {'name': 'unknown'})
            relocations.append({'got_address': r_offset, 'symbol': symbol['name']})
        return relocations

    def _analyze_plt(self) -> List[Dict[str, Any]]:
        plt_sec = self.get_section('.plt')
        if not plt_sec:
            logger.warning("No .plt section found in %s", self.file_path)
            return []
        if not capstone:
            logger.error("Capstone is not available. Please install with: pip install capstone")
            return []

        self.file_handle.seek(plt_sec['offset'])
        plt_data = self.file_handle.read(plt_sec['size'])

        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        md.detail = True

        results = []
        entry_size = 16

        for i in range(0, plt_sec['size'], entry_size):
            entry_addr = plt_sec['addr'] + i
            entry_data = plt_data[i:i + entry_size]

            symbol = "PLT[0] (Resolver)" if i == 0 else f"unknown_plt_{i // entry_size}"

            if i > 0:
                for insn in md.disasm(entry_data, entry_addr):
                    if insn.mnemonic == 'jmp' and len(insn.operands) > 0:
                        op = insn.operands[0]
                        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                            target_got = insn.address + insn.size + op.mem.disp
                            symbol = self.reloc_map.get(target_got, symbol)
                            break

            results.append(
                {'index': i // entry_size, 'address': f"0x{entry_addr:x}", 'symbol': symbol, 'size': entry_size})

        return results

    @staticmethod
    def analyze_plt_and_got(file_path: str) -> List[Dict[str, Any]]:
        try:
            parser = BinaryParser._get_parser_instance(file_path)
            return parser._analyze_plt()
        except (IOError, ValueError) as e:
            logger.error("Failed to parse %s: %s", file_path, e)
            return []
