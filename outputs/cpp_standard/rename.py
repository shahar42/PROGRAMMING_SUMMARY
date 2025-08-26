#!/usr/bin/env python3
"""
Optimized JSON Concept File Renamer for MCP System
Renames concept files to match system architecture for maximum query efficiency
Preserves API compatibility through mapping files
"""

import json
import os
import re
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

class MCPConceptRenamer:
    """Renames concept JSON files for optimal MCP system performance"""
    
    def __init__(self, project_root: str = "/home/shahar42/Suumerizing_C_holy_grale_book", dry_run: bool = False):
        self.project_root = Path(project_root)
        self.outputs_dir = self.project_root / "outputs"
        self.backup_dir = self.project_root / f"backups/rename_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.mapping_file = self.project_root / "file_name_mapping.json"
        self.dry_run = dry_run
        
        # Book code mappings for MCP orchestrator compatibility
        self.book_codes = {
            'kernighan_ritchie': 'kr',
            'unix_env': 'unix',
            'linkers_loaders': 'link',
            'os_three_pieces': 'os',
            'expert_c_programming': 'exp',
            'csapp': 'csapp',
            'cpp_standard': 'cpp',
            'cpp_primer': 'cppx'
        }
        
        # Category detection patterns
        self.category_patterns = {
            'mem': ['malloc', 'free', 'memory', 'heap', 'stack', 'allocation', 'realloc', 'calloc', 'mmap', 'munmap', 'brk', 'sbrk', 'mlock', 'munlock', 'mprotect', 'alloc'],
            'ptr': ['pointer', '*', 'dereference', 'address', '->', 'reference'],
            'func': ['function', 'return', 'parameter', 'argument', 'call', 'prototype', 'recursion'],
            'io': ['printf', 'scanf', 'file', 'stream', 'input', 'output', 'read', 'write', 'fopen', 'open', 'close', 'lseek', 'fcntl', 'ioctl', 'pipe', 'dup', 'sync'],
            'proc': ['fork', 'exec', 'process', 'pid', 'wait', 'signal', 'kill', 'exit', 'clone', 'getpid', 'getppid', 'setpgid', 'getpgid', 'session', 'setsid', 'getsid'],
            'thread': ['thread', 'pthread', 'mutex', 'semaphore', 'concurrent', 'lock', 'synchronization', 'futex'],
            'net': ['socket', 'tcp', 'udp', 'network', 'port', 'connection', 'bind', 'listen', 'accept', 'connect', 'send', 'recv', 'sendto', 'recvfrom', 'sendmsg', 'recvmsg'],
            'sys': ['system', 'kernel', 'syscall', 'interrupt', 'driver', 'ioctl', 'sysctl', 'prctl', 'arch_prctl', 'personality', 'uname', 'sysinfo'],
            'struct': ['struct', 'union', 'typedef', 'enum', 'data structure', 'field'],
            'ctrl': ['if', 'while', 'for', 'loop', 'switch', 'goto', 'break', 'continue'],
            'op': ['operator', '+', '-', '*', '/', '%', '&', '|', '^', '<<', '>>', '++', '--'],
            'link': ['linker', 'loader', 'symbol', 'relocation', 'library', '.so', '.a', 'elf', 'module'],
            'syn': ['syntax', 'declaration', 'definition', 'statement', 'expression', 'grammar'],
            'bin': ['binary', 'got', 'plt', 'relocation', 'segment', 'section', 'object file'],
            'fs': ['filesystem', 'directory', 'file', 'path', 'mount', 'umount', 'chdir', 'mkdir', 'rmdir', 'link', 'unlink', 'chmod', 'chown', 'stat', 'access', 'truncate'],
            'time': ['time', 'clock', 'timer', 'nanosleep', 'alarm', 'gettime', 'settime', 'gettimeofday', 'settimeofday'],
            'ipc': ['ipc', 'message', 'queue', 'semaphore', 'shared', 'memory', 'msgget', 'msgctl', 'msgsnd', 'msgrcv', 'semget', 'semctl', 'semop', 'shmget', 'shmat', 'shmdt'],
            'user': ['user', 'group', 'uid', 'gid', 'getuid', 'setuid', 'getgid', 'setgid', 'geteuid', 'seteuid', 'getegid', 'setegid', 'getgroups', 'setgroups'],
            'security': ['security', 'capability', 'permission', 'audit', 'keyring', 'seccomp', 'landlock', 'cap'],
            'event': ['event', 'poll', 'select', 'epoll', 'inotify', 'eventfd', 'signalfd', 'timerfd']
        }
        
        # Track renaming operations
        self.rename_map = {}  # old_path -> new_path
        self.stats = {
            'files_processed': 0,
            'files_renamed': 0,
            'files_skipped': 0,
            'duplicates_found': 0,
            'errors': 0
        }
        
    def run(self):
        """Execute the renaming process"""
        print(f"{'🔍 DRY RUN MODE' if self.dry_run else '🚀 RENAMING MODE'}")
        print(f"📁 Processing concepts in: {self.outputs_dir}")
        
        # Step 1: Create backup (skip in dry run)
        if not self.dry_run:
            if not self.create_backup():
                print("❌ Backup failed. Aborting.")
                return False
        
        # Step 2: Load existing mapping if it exists
        self.load_existing_mapping()
        
        # Step 3: Process all concept files
        # Skip linkers_loaders, kernighan_ritchie, and posix_manpages directories
        excluded_dirs = {'linkers_loaders', 'kernighan_ritchie', 'posix_manpages'}
        
        for book_dir in sorted(self.outputs_dir.iterdir()):
            if book_dir.is_dir() and book_dir.name not in excluded_dirs:
                self.process_book_directory(book_dir)
        
        # Step 4: Save mapping file (skip in dry run)
        if not self.dry_run:
            self.save_mapping_file()
        
        # Step 5: Print summary
        self.print_summary()
        
        return True
    
    def create_backup(self) -> bool:
        """Create complete backup of outputs directory"""
        print("📦 Creating backup...")
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy entire outputs directory
            backup_outputs = self.backup_dir / "outputs"
            shutil.copytree(self.outputs_dir, backup_outputs)
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'original_structure': self._capture_structure()
            }
            
            with open(self.backup_dir / "backup_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup created: {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def _capture_structure(self) -> Dict:
        """Capture current file structure"""
        structure = {}
        for book_dir in self.outputs_dir.iterdir():
            if book_dir.is_dir():
                structure[book_dir.name] = [f.name for f in book_dir.glob("*.json")]
        return structure
    
    def load_existing_mapping(self):
        """Load existing file mapping if it exists"""
        if self.mapping_file.exists():
            with open(self.mapping_file, 'r') as f:
                existing = json.load(f)
                # Only load mappings, not overwrite our new ones
                if 'mappings' in existing:
                    print(f"📋 Loaded {len(existing['mappings'])} existing mappings")
    
    def process_book_directory(self, book_dir: Path):
        """Process all concept files in a book directory"""
        book_name = book_dir.name
        book_code = self.book_codes.get(book_name, book_name[:4])
        
        print(f"\n📚 Processing {book_name} (code: {book_code})")
        
        json_files = sorted(book_dir.glob("*.json"))
        print(f"  Found {len(json_files)} JSON files")
        
        for json_file in json_files:
            self.process_concept_file(json_file, book_name, book_code)
    
    def process_concept_file(self, file_path: Path, book_name: str, book_code: str):
        """Process and rename a single concept file"""
        self.stats['files_processed'] += 1
        
        try:
            # Load concept data
            with open(file_path, 'r', encoding='utf-8') as f:
                concept_data = json.load(f)
            
            # Generate new name
            new_name = self.generate_optimized_name(concept_data, book_code, file_path)
            
            if new_name == file_path.name:
                self.stats['files_skipped'] += 1
                return
            
            new_path = file_path.parent / new_name
            
            # Check for duplicates
            if new_path.exists() and new_path != file_path:
                self.stats['duplicates_found'] += 1
                # Add hash to make unique
                hash_suffix = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                new_name = new_name.replace('.json', f'_{hash_suffix}.json')
                new_path = file_path.parent / new_name
            
            # Store mapping
            self.rename_map[str(file_path.relative_to(self.project_root))] = str(new_path.relative_to(self.project_root))
            
            # Perform rename (skip in dry run)
            if not self.dry_run:
                file_path.rename(new_path)
                print(f"  ✅ {file_path.name} → {new_name}")
            else:
                print(f"  🔍 Would rename: {file_path.name} → {new_name}")
            
            self.stats['files_renamed'] += 1
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            self.stats['errors'] += 1
    
    def generate_optimized_name(self, concept_data: Dict, book_code: str, original_path: Path) -> str:
        """
        Generate optimized filename following the pattern:
        {book_code}_{category}_{normalized_topic}_{uniqueid}.json
        """
        # Extract concept information (handle different JSON structures)
        if 'name' in concept_data:
            # Unix/POSIX system call format
            topic = concept_data.get('name', 'unknown')
            explanation = concept_data.get('description', '')
            code_example = concept_data.get('synopsis', [])
        else:
            # Standard concept format
            topic = concept_data.get('topic', 'unknown')
            explanation = concept_data.get('explanation', '')
            code_example = concept_data.get('code_example', [])
        
        # Detect category
        category = self.detect_category(topic, explanation, code_example)
        
        # Normalize topic (matching ConceptMemoryManager's normalization)
        normalized_topic = self.normalize_topic(topic)
        
        # Limit topic length
        if len(normalized_topic) > 40:
            normalized_topic = normalized_topic[:40]
        
        # Generate unique ID (6-char hash of content)
        content_hash = hashlib.md5(
            f"{topic}{explanation}{str(code_example)}".encode()
        ).hexdigest()[:6]
        
        # Build filename
        new_name = f"{book_code}_{category}_{normalized_topic}_{content_hash}.json"
        
        # Clean up any double underscores
        new_name = re.sub(r'_{2,}', '_', new_name)
        
        return new_name
    
    def detect_category(self, topic: str, explanation: str, code_example: List) -> str:
        """Detect category based on concept content"""
        # Combine all text for analysis
        text = f"{topic} {explanation} {' '.join(code_example) if code_example else ''}".lower()
        
        # Score each category
        category_scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = sum(1 for pattern in patterns if pattern.lower() in text)
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category, or 'core' as default
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        # Default category based on common patterns
        if any(kw in text for kw in ['variable', 'declaration', 'type', 'const']):
            return 'var'
        elif any(kw in text for kw in ['algorithm', 'sort', 'search', 'tree']):
            return 'algo'
        else:
            return 'core'
    
    def normalize_topic(self, topic: str) -> str:
        """
        Normalize topic to match ConceptMemoryManager's normalization
        This ensures filesystem names match the in-memory index
        """
        # Convert to lowercase
        normalized = topic.lower().strip()
        
        # Replace spaces and hyphens with underscores
        normalized = re.sub(r'[\s\-]+', '_', normalized)
        
        # Remove special characters except underscores
        normalized = re.sub(r'[^\w_]', '', normalized)
        
        # Remove multiple underscores
        normalized = re.sub(r'_{2,}', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized if normalized else 'concept'
    
    def save_mapping_file(self):
        """Save the complete file name mapping"""
        mapping_data = {
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'description': 'MCP-optimized concept file naming',
            'stats': self.stats,
            'mappings': self.rename_map,
            'reverse_mappings': {v: k for k, v in self.rename_map.items()}
        }
        
        with open(self.mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        print(f"\n📋 Mapping saved to: {self.mapping_file}")
    
    def print_summary(self):
        """Print operation summary"""
        print("\n" + "="*60)
        print("📊 RENAMING SUMMARY")
        print("="*60)
        print(f"Files processed:  {self.stats['files_processed']}")
        print(f"Files renamed:    {self.stats['files_renamed']}")
        print(f"Files skipped:    {self.stats['files_skipped']}")
        print(f"Duplicates found: {self.stats['duplicates_found']}")
        print(f"Errors:           {self.stats['errors']}")
        
        if not self.dry_run:
            print(f"\n✅ Renaming complete!")
            print(f"📦 Backup location: {self.backup_dir}")
            print(f"📋 Mapping file: {self.mapping_file}")
        else:
            print(f"\n🔍 Dry run complete. No files were actually renamed.")
            print(f"   Run without --dry-run to perform actual renaming.")
    
    def restore_from_backup(self, backup_path: str):
        """Restore original file names from backup"""
        backup_dir = Path(backup_path)
        backup_outputs = backup_dir / "outputs"
        
        if not backup_outputs.exists():
            print(f"❌ Backup not found: {backup_outputs}")
            return False
        
        print(f"🔄 Restoring from backup: {backup_dir}")
        
        # Remove current outputs
        if self.outputs_dir.exists():
            shutil.rmtree(self.outputs_dir)
        
        # Copy backup back
        shutil.copytree(backup_outputs, self.outputs_dir)
        
        print(f"✅ Restored from backup successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description='Rename concept JSON files for optimal MCP system performance')
    parser.add_argument('--project-root', type=str, 
                       default='/home/shahar42/Suumerizing_C_holy_grale_book',
                       help='Project root directory')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be renamed without actually renaming')
    parser.add_argument('--restore', type=str, metavar='BACKUP_PATH',
                       help='Restore from a specific backup')
    
    args = parser.parse_args()
    
    renamer = MCPConceptRenamer(
        project_root=args.project_root,
        dry_run=args.dry_run
    )
    
    if args.restore:
        renamer.restore_from_backup(args.restore)
    else:
        renamer.run()


if __name__ == "__main__":
    main()
