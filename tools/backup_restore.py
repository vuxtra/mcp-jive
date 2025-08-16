#!/usr/bin/env python3
"""
Backup and Restore Utility

Provides backup and restore functionality for MCP Jive data and configuration.
"""

import sys
import os
import json
import shutil
import tarfile
import argparse
import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Project root directory
project_root = Path(__file__).parent.parent

def main():
    parser = argparse.ArgumentParser(description="Backup and restore MCP Jive data")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("--output", "-o", type=str,
                              help="Output backup file path")
    backup_parser.add_argument("--include-data", action="store_true", default=True,
                              help="Include data directory (default: true)")
    backup_parser.add_argument("--include-config", action="store_true", default=True,
                              help="Include configuration files (default: true)")
    backup_parser.add_argument("--include-logs", action="store_true",
                              help="Include log files")
    backup_parser.add_argument("--compress", "-c", action="store_true", default=True,
                              help="Compress backup (default: true)")
    backup_parser.add_argument("--exclude", action="append", default=[],
                              help="Exclude patterns (can be used multiple times)")
    backup_parser.add_argument("--description", "-d", type=str,
                              help="Backup description")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_file", type=str,
                               help="Backup file to restore from")
    restore_parser.add_argument("--force", "-f", action="store_true",
                               help="Force restore (overwrite existing files)")
    restore_parser.add_argument("--selective", "-s", action="store_true",
                               help="Selective restore (choose what to restore)")
    restore_parser.add_argument("--dry-run", action="store_true",
                               help="Show what would be restored without doing it")
    restore_parser.add_argument("--target-dir", type=str,
                               help="Target directory for restore (default: current)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List backup contents")
    list_parser.add_argument("backup_file", type=str,
                            help="Backup file to examine")
    list_parser.add_argument("--detailed", "-d", action="store_true",
                            help="Show detailed information")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_file", type=str,
                              help="Backup file to verify")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean old backups")
    clean_parser.add_argument("--days", "-d", type=int, default=30,
                             help="Delete backups older than N days (default: 30)")
    clean_parser.add_argument("--keep", "-k", type=int, default=5,
                             help="Keep at least N most recent backups (default: 5)")
    clean_parser.add_argument("--backup-dir", type=str,
                             help="Backup directory to clean (default: ./backups)")
    clean_parser.add_argument("--dry-run", action="store_true",
                             help="Show what would be deleted without doing it")
    
    # Global options
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress non-error output")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    backup_tool = BackupRestoreTool(
        verbose=args.verbose,
        quiet=args.quiet
    )
    
    try:
        if args.command == "backup":
            return backup_tool.create_backup(
                output_path=args.output,
                include_data=args.include_data,
                include_config=args.include_config,
                include_logs=args.include_logs,
                compress=args.compress,
                exclude_patterns=args.exclude,
                description=args.description
            )
        elif args.command == "restore":
            return backup_tool.restore_backup(
                backup_file=args.backup_file,
                force=args.force,
                selective=args.selective,
                dry_run=args.dry_run,
                target_dir=args.target_dir
            )
        elif args.command == "list":
            return backup_tool.list_backup(
                backup_file=args.backup_file,
                detailed=args.detailed
            )
        elif args.command == "verify":
            return backup_tool.verify_backup(args.backup_file)
        elif args.command == "clean":
            return backup_tool.clean_backups(
                days=args.days,
                keep=args.keep,
                backup_dir=args.backup_dir,
                dry_run=args.dry_run
            )
    except KeyboardInterrupt:
        backup_tool.log("\nOperation interrupted by user")
        return 130
    except Exception as e:
        backup_tool.log(f"Error: {e}", "error")
        return 1

class BackupRestoreTool:
    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.project_root = project_root
        
    def log(self, message, level="info"):
        """Log a message"""
        if self.quiet and level != "error":
            return
            
        if level == "error":
            print(f"❌ {message}", file=sys.stderr)
        elif level == "warning":
            print(f"⚠️  {message}")
        elif level == "success":
            print(f"✅ {message}")
        elif self.verbose or level == "info":
            print(f"ℹ️  {message}")
    
    def create_backup(self, output_path=None, include_data=True, include_config=True,
                     include_logs=False, compress=True, exclude_patterns=None,
                     description=None):
        """Create a backup"""
        if exclude_patterns is None:
            exclude_patterns = []
        
        # Generate backup filename if not provided
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.project_root / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            extension = ".tar.gz" if compress else ".tar"
            output_path = backup_dir / f"mcp_jive_backup_{timestamp}{extension}"
        else:
            output_path = Path(output_path)
        
        self.log(f"Creating backup: {output_path}")
        
        # Create backup metadata
        metadata = {
            "created_at": datetime.datetime.now().isoformat(),
            "description": description or "MCP Jive backup",
            "includes": {
                "data": include_data,
                "config": include_config,
                "logs": include_logs
            },
            "exclude_patterns": exclude_patterns,
            "version": "1.0"
        }
        
        # Determine compression mode
        mode = "w:gz" if compress else "w"
        
        try:
            with tarfile.open(output_path, mode) as tar:
                # Add metadata
                metadata_json = json.dumps(metadata, indent=2)
                metadata_info = tarfile.TarInfo(name="backup_metadata.json")
                metadata_info.size = len(metadata_json.encode())
                tar.addfile(metadata_info, fileobj=None)
                
                # Add files based on options
                files_added = 0
                
                if include_data:
                    data_dir = self.project_root / "data"
                    if data_dir.exists():
                        files_added += self._add_directory_to_tar(
                            tar, data_dir, "data", exclude_patterns
                        )
                
                if include_config:
                    # Add .env file
                    env_file = self.project_root / ".env"
                    if env_file.exists():
                        tar.add(env_file, arcname=".env")
                        files_added += 1
                    
                    # Add config directory
                    config_dir = self.project_root / "config"
                    if config_dir.exists():
                        files_added += self._add_directory_to_tar(
                            tar, config_dir, "config", exclude_patterns
                        )
                
                if include_logs:
                    logs_dir = self.project_root / "logs"
                    if logs_dir.exists():
                        files_added += self._add_directory_to_tar(
                            tar, logs_dir, "logs", exclude_patterns
                        )
                
                self.log(f"Added {files_added} files to backup")
        
        except Exception as e:
            self.log(f"Failed to create backup: {e}", "error")
            return 1
        
        # Get backup size
        backup_size = output_path.stat().st_size
        size_mb = backup_size / (1024 * 1024)
        
        self.log(f"Backup created successfully: {output_path}", "success")
        self.log(f"Backup size: {size_mb:.2f} MB")
        
        return 0
    
    def _add_directory_to_tar(self, tar, directory, arcname, exclude_patterns):
        """Add directory to tar archive"""
        files_added = 0
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Check exclude patterns
                relative_path = file_path.relative_to(self.project_root)
                if self._should_exclude(str(relative_path), exclude_patterns):
                    continue
                
                arc_path = arcname + "/" + str(file_path.relative_to(directory))
                tar.add(file_path, arcname=arc_path)
                files_added += 1
                
                if self.verbose:
                    self.log(f"Added: {arc_path}")
        
        return files_added
    
    def _should_exclude(self, file_path, exclude_patterns):
        """Check if file should be excluded"""
        import fnmatch
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        # Default exclusions
        default_exclusions = [
            "*.pyc",
            "__pycache__/*",
            "*.tmp",
            "*.log",
            ".DS_Store"
        ]
        
        for pattern in default_exclusions:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def restore_backup(self, backup_file, force=False, selective=False,
                      dry_run=False, target_dir=None):
        """Restore from backup"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            self.log(f"Backup file not found: {backup_path}", "error")
            return 1
        
        target_path = Path(target_dir) if target_dir else self.project_root
        
        self.log(f"Restoring from backup: {backup_path}")
        self.log(f"Target directory: {target_path}")
        
        if dry_run:
            self.log("DRY RUN - No files will be modified")
        
        try:
            with tarfile.open(backup_path, "r:*") as tar:
                # Read metadata
                try:
                    metadata_member = tar.getmember("backup_metadata.json")
                    metadata_file = tar.extractfile(metadata_member)
                    metadata = json.loads(metadata_file.read().decode())
                    
                    self.log(f"Backup created: {metadata['created_at']}")
                    self.log(f"Description: {metadata['description']}")
                    
                except KeyError:
                    self.log("No metadata found in backup", "warning")
                    metadata = {}
                
                # Get list of members to restore
                members = tar.getmembers()
                files_to_restore = [m for m in members if m.name != "backup_metadata.json"]
                
                if selective:
                    files_to_restore = self._select_files_for_restore(files_to_restore)
                
                # Check for conflicts
                conflicts = []
                for member in files_to_restore:
                    target_file = target_path / member.name
                    if target_file.exists() and not force:
                        conflicts.append(member.name)
                
                if conflicts and not force:
                    self.log(f"Found {len(conflicts)} conflicting files:", "warning")
                    for conflict in conflicts[:5]:  # Show first 5
                        self.log(f"  {conflict}")
                    if len(conflicts) > 5:
                        self.log(f"  ... and {len(conflicts) - 5} more")
                    self.log("Use --force to overwrite existing files")
                    return 1
                
                # Perform restore
                if not dry_run:
                    for member in files_to_restore:
                        tar.extract(member, target_path)
                        if self.verbose:
                            self.log(f"Restored: {member.name}")
                
                self.log(f"Restored {len(files_to_restore)} files", "success")
        
        except Exception as e:
            self.log(f"Failed to restore backup: {e}", "error")
            return 1
        
        return 0
    
    def _select_files_for_restore(self, members):
        """Interactive file selection for restore"""
        print("\nSelect files to restore:")
        print("(Enter numbers separated by spaces, or 'all' for all files)")
        
        for i, member in enumerate(members, 1):
            print(f"{i:3d}. {member.name}")
        
        try:
            selection = input("\nSelection: ").strip()
            
            if selection.lower() == "all":
                return members
            
            indices = [int(x) - 1 for x in selection.split()]
            return [members[i] for i in indices if 0 <= i < len(members)]
        
        except (ValueError, KeyboardInterrupt):
            return []
    
    def list_backup(self, backup_file, detailed=False):
        """List backup contents"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            self.log(f"Backup file not found: {backup_path}", "error")
            return 1
        
        try:
            with tarfile.open(backup_path, "r:*") as tar:
                # Show metadata
                try:
                    metadata_member = tar.getmember("backup_metadata.json")
                    metadata_file = tar.extractfile(metadata_member)
                    metadata = json.loads(metadata_file.read().decode())
                    
                    print(f"Backup Information:")
                    print(f"  Created: {metadata['created_at']}")
                    print(f"  Description: {metadata['description']}")
                    print(f"  Includes: {', '.join([k for k, v in metadata['includes'].items() if v])}")
                    print()
                    
                except KeyError:
                    print("No metadata found in backup\n")
                
                # List contents
                members = [m for m in tar.getmembers() if m.name != "backup_metadata.json"]
                
                print(f"Contents ({len(members)} files):")
                
                if detailed:
                    for member in members:
                        size_kb = member.size / 1024
                        mtime = datetime.datetime.fromtimestamp(member.mtime)
                        print(f"  {member.name:<50} {size_kb:>8.1f} KB  {mtime.strftime('%Y-%m-%d %H:%M')}")
                else:
                    for member in members:
                        print(f"  {member.name}")
        
        except Exception as e:
            self.log(f"Failed to list backup: {e}", "error")
            return 1
        
        return 0
    
    def verify_backup(self, backup_file):
        """Verify backup integrity"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            self.log(f"Backup file not found: {backup_path}", "error")
            return 1
        
        self.log(f"Verifying backup: {backup_path}")
        
        try:
            with tarfile.open(backup_path, "r:*") as tar:
                # Check if we can read all members
                members = tar.getmembers()
                errors = 0
                
                for member in members:
                    try:
                        if member.isfile():
                            # Try to extract file data
                            tar.extractfile(member).read()
                    except Exception as e:
                        self.log(f"Error reading {member.name}: {e}", "error")
                        errors += 1
                
                if errors == 0:
                    self.log(f"Backup verification successful ({len(members)} files)", "success")
                    return 0
                else:
                    self.log(f"Backup verification failed ({errors} errors)", "error")
                    return 1
        
        except Exception as e:
            self.log(f"Failed to verify backup: {e}", "error")
            return 1
    
    def clean_backups(self, days=30, keep=5, backup_dir=None, dry_run=False):
        """Clean old backups"""
        if backup_dir:
            backup_path = Path(backup_dir)
        else:
            backup_path = self.project_root / "backups"
        
        if not backup_path.exists():
            self.log(f"Backup directory not found: {backup_path}")
            return 0
        
        self.log(f"Cleaning backups in: {backup_path}")
        
        if dry_run:
            self.log("DRY RUN - No files will be deleted")
        
        # Find backup files
        backup_files = list(backup_path.glob("*.tar*"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Calculate cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        files_to_delete = []
        
        # Keep most recent files
        files_to_check = backup_files[keep:] if len(backup_files) > keep else []
        
        for backup_file in files_to_check:
            mtime = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            if mtime < cutoff_date:
                files_to_delete.append(backup_file)
        
        if not files_to_delete:
            self.log("No backups to clean")
            return 0
        
        self.log(f"Found {len(files_to_delete)} backups to delete:")
        total_size = 0
        
        for backup_file in files_to_delete:
            size = backup_file.stat().st_size
            total_size += size
            mtime = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            size_mb = size / (1024 * 1024)
            
            self.log(f"  {backup_file.name} ({size_mb:.1f} MB, {mtime.strftime('%Y-%m-%d')})")
            
            if not dry_run:
                try:
                    backup_file.unlink()
                except Exception as e:
                    self.log(f"Failed to delete {backup_file.name}: {e}", "error")
        
        total_mb = total_size / (1024 * 1024)
        action = "Would free" if dry_run else "Freed"
        self.log(f"{action} {total_mb:.1f} MB of disk space", "success")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())