"""
File management utilities for workflow saving, loading, and operations.
Provides secure file operations with validation and backup support.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import zipfile
import hashlib
import logging

from workflow.serializer import WorkflowSerializer

class FileManagerError(Exception):
    """Custom exception for file manager errors."""
    pass

class BackupManager:
    """Manages backup operations for workflow files."""
    
    def __init__(self, backup_dir: Optional[str] = None, max_backups: int = 10):
        """Initialize backup manager."""
        self.max_backups = max_backups
        
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path.home() / ".workflow_builder" / "backups"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, file_path: str, backup_suffix: str = "") -> str:
        """Create backup of a file."""
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileManagerError(f"Source file not found: {file_path}")
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.stem}_{timestamp}{backup_suffix}{source_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # Copy file to backup location
        shutil.copy2(source_path, backup_path)
        
        # Clean up old backups
        self._cleanup_old_backups(source_path.stem)
        
        return str(backup_path)
    
    def _cleanup_old_backups(self, base_name: str):
        """Remove old backup files beyond max_backups limit."""
        backup_pattern = f"{base_name}_*"
        backup_files = list(self.backup_dir.glob(backup_pattern))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess backups
        for backup_file in backup_files[self.max_backups:]:
            try:
                backup_file.unlink()
            except OSError:
                pass  # Ignore errors when deleting old backups
    
    def list_backups(self, base_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        if base_name:
            pattern = f"{base_name}_*"
        else:
            pattern = "*"
        
        backup_files = list(self.backup_dir.glob(pattern))
        backups = []
        
        for backup_file in backup_files:
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime),
                "base_name": backup_file.stem.split("_")[0]
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore a backup to target location."""
        try:
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            raise FileManagerError(f"Failed to restore backup: {str(e)}")

class FileManager:
    """Comprehensive file manager for workflow operations."""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        """Initialize file manager."""
        self.logger = logging.getLogger(__name__)
        self.serializer = WorkflowSerializer()
        
        # Set up workspace directory
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
        else:
            self.workspace_dir = Path.home() / ".workflow_builder" / "workspace"
        
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize backup manager
        self.backup_manager = BackupManager()
        
        # Current file tracking
        self.current_file_path: Optional[str] = None
        self.file_history: List[str] = []
        
        # File watching
        self._file_checksums: Dict[str, str] = {}
    
    def set_workspace(self, workspace_path: str):
        """Set the workspace directory."""
        self.workspace_dir = Path(workspace_path)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Workspace set to: {workspace_path}")
    
    def save_workflow(self, workflow_data: Dict[str, Any], file_path: str,
                     create_backup: bool = True) -> bool:
        """Save workflow to file with optional backup."""
        try:
            file_path = Path(file_path)
            
            # Create backup if file exists and backup is requested
            if create_backup and file_path.exists():
                try:
                    backup_path = self.backup_manager.create_backup(str(file_path))
                    self.logger.info(f"Backup created: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to create backup: {str(e)}")
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare metadata
            metadata = {
                "name": workflow_data.get("metadata", {}).get("name", file_path.stem),
                "saved_at": datetime.now().isoformat(),
                "file_path": str(file_path)
            }
            
            # Use temporary file for atomic write
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', 
                                           dir=file_path.parent, delete=False) as tmp_file:
                temp_path = tmp_file.name
                
                # Serialize and save
                self.serializer.save_to_file(workflow_data, temp_path, metadata)
            
            # Atomic move to final location
            shutil.move(temp_path, file_path)
            
            # Update tracking
            self.current_file_path = str(file_path)
            self._update_file_checksum(str(file_path))
            self._add_to_history(str(file_path))
            
            self.logger.info(f"Workflow saved: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow: {str(e)}")
            
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals():
                    Path(temp_path).unlink(missing_ok=True)
            except:
                pass
            
            raise FileManagerError(f"Failed to save workflow: {str(e)}")
    
    def load_workflow(self, file_path: str) -> Dict[str, Any]:
        """Load workflow from file."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileManagerError(f"File not found: {file_path}")
            
            if not file_path.is_file():
                raise FileManagerError(f"Path is not a file: {file_path}")
            
            # Check file size (basic security measure)
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                raise FileManagerError("File too large (>100MB)")
            
            # Load and validate
            workflow_data = self.serializer.load_from_file(str(file_path))
            
            # Update tracking
            self.current_file_path = str(file_path)
            self._update_file_checksum(str(file_path))
            self._add_to_history(str(file_path))
            
            self.logger.info(f"Workflow loaded: {file_path}")
            return workflow_data
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {str(e)}")
            raise FileManagerError(f"Failed to load workflow: {str(e)}")
    
    def export_workflow(self, workflow_data: Dict[str, Any], export_path: str,
                       export_format: str = "json") -> bool:
        """Export workflow in various formats."""
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            if export_format == "json":
                exported_data = self.serializer.export_to_format(workflow_data, "json")
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(exported_data)
            
            elif export_format == "yaml":
                exported_data = self.serializer.export_to_format(workflow_data, "yaml")
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(exported_data)
            
            elif export_format == "summary":
                summary = self.serializer.export_to_format(workflow_data, "summary")
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
            
            elif export_format == "zip":
                self._export_as_zip(workflow_data, export_path)
            
            else:
                raise FileManagerError(f"Unsupported export format: {export_format}")
            
            self.logger.info(f"Workflow exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export workflow: {str(e)}")
            raise FileManagerError(f"Failed to export workflow: {str(e)}")
    
    def _export_as_zip(self, workflow_data: Dict[str, Any], zip_path: Path):
        """Export workflow as ZIP archive with assets."""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main workflow file
            workflow_json = self.serializer.export_to_format(workflow_data, "json")
            zip_file.writestr("workflow.json", workflow_json)
            
            # Add summary
            summary = self.serializer.export_to_format(workflow_data, "summary")
            zip_file.writestr("README.txt", summary)
            
            # Add metadata
            metadata = {
                "export_date": datetime.now().isoformat(),
                "format_version": "1.0",
                "exported_by": "Workflow Builder"
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    def import_workflow(self, import_path: str) -> Dict[str, Any]:
        """Import workflow from various formats."""
        try:
            import_path = Path(import_path)
            
            if not import_path.exists():
                raise FileManagerError(f"Import file not found: {import_path}")
            
            if import_path.suffix.lower() == '.zip':
                return self._import_from_zip(import_path)
            else:
                # Try to load as JSON workflow
                return self.load_workflow(str(import_path))
                
        except Exception as e:
            self.logger.error(f"Failed to import workflow: {str(e)}")
            raise FileManagerError(f"Failed to import workflow: {str(e)}")
    
    def _import_from_zip(self, zip_path: Path) -> Dict[str, Any]:
        """Import workflow from ZIP archive."""
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Look for workflow file
            workflow_files = [name for name in zip_file.namelist() 
                            if name.endswith('.json') and 'workflow' in name.lower()]
            
            if not workflow_files:
                raise FileManagerError("No workflow file found in ZIP archive")
            
            # Read workflow data
            workflow_content = zip_file.read(workflow_files[0])
            workflow_data = json.loads(workflow_content.decode('utf-8'))
            
            return self.serializer.deserialize_workflow(workflow_data)
    
    def list_workspace_files(self, pattern: str = "*.wf.json") -> List[Dict[str, Any]]:
        """List workflow files in workspace."""
        files = []
        
        for file_path in self.workspace_dir.glob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                
                # Try to get workflow metadata
                metadata = {"name": file_path.stem}
                try:
                    workflow_data = self.serializer.load_from_file(str(file_path))
                    metadata.update(workflow_data.get("metadata", {}))
                except:
                    pass  # Use default metadata if file can't be loaded
                
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "metadata": metadata
                })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def create_new_workflow(self, name: str = "New Workflow") -> Dict[str, Any]:
        """Create a new empty workflow."""
        template = self.serializer.create_workflow_template(name)
        return template
    
    def duplicate_workflow(self, source_path: str, new_name: Optional[str] = None) -> str:
        """Duplicate an existing workflow."""
        try:
            # Load source workflow
            workflow_data = self.load_workflow(source_path)
            
            # Update metadata
            if new_name:
                workflow_data["metadata"]["name"] = new_name
            else:
                original_name = workflow_data["metadata"].get("name", "Workflow")
                workflow_data["metadata"]["name"] = f"{original_name} (Copy)"
            
            workflow_data["metadata"]["created_at"] = datetime.now().isoformat()
            workflow_data["metadata"]["modified_at"] = datetime.now().isoformat()
            
            # Generate new file path
            source_path_obj = Path(source_path)
            if new_name:
                safe_name = self._sanitize_filename(new_name)
                new_path = source_path_obj.parent / f"{safe_name}.wf.json"
            else:
                new_path = source_path_obj.parent / f"{source_path_obj.stem}_copy.wf.json"
            
            # Ensure unique filename
            counter = 1
            while new_path.exists():
                if new_name:
                    safe_name = self._sanitize_filename(new_name)
                    new_path = source_path_obj.parent / f"{safe_name}_{counter}.wf.json"
                else:
                    new_path = source_path_obj.parent / f"{source_path_obj.stem}_copy_{counter}.wf.json"
                counter += 1
            
            # Save duplicated workflow
            self.save_workflow(workflow_data, str(new_path))
            
            return str(new_path)
            
        except Exception as e:
            raise FileManagerError(f"Failed to duplicate workflow: {str(e)}")
    
    def delete_workflow(self, file_path: str, create_backup: bool = True) -> bool:
        """Delete a workflow file with optional backup."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileManagerError(f"File not found: {file_path}")
            
            # Create backup before deletion
            if create_backup:
                backup_path = self.backup_manager.create_backup(str(file_path), "_deleted")
                self.logger.info(f"Backup created before deletion: {backup_path}")
            
            # Delete file
            file_path.unlink()
            
            # Update tracking
            if self.current_file_path == str(file_path):
                self.current_file_path = None
            
            self.logger.info(f"Workflow deleted: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete workflow: {str(e)}")
            raise FileManagerError(f"Failed to delete workflow: {str(e)}")
    
    def has_unsaved_changes(self) -> bool:
        """Check if current file has unsaved changes."""
        if not self.current_file_path:
            return False
        
        current_checksum = self._calculate_file_checksum(self.current_file_path)
        stored_checksum = self._file_checksums.get(self.current_file_path)
        
        return current_checksum != stored_checksum
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a workflow file."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileManagerError(f"File not found: {file_path}")
            
            stat = file_path.stat()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "checksum": self._calculate_file_checksum(str(file_path))
            }
            
            # Try to get workflow metadata
            try:
                workflow_data = self.serializer.load_from_file(str(file_path))
                info["metadata"] = workflow_data.get("metadata", {})
                info["node_count"] = len(workflow_data.get("nodes", {}))
                info["connection_count"] = len(workflow_data.get("connections", {}))
                info["version"] = workflow_data.get("version", "unknown")
            except Exception as e:
                info["error"] = f"Failed to read workflow data: {str(e)}"
            
            return info
            
        except Exception as e:
            raise FileManagerError(f"Failed to get file info: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Trim whitespace and dots
        filename = filename.strip('. ')
        
        # Ensure not empty
        if not filename:
            filename = "untitled"
        
        return filename
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _update_file_checksum(self, file_path: str):
        """Update stored checksum for file."""
        checksum = self._calculate_file_checksum(file_path)
        self._file_checksums[file_path] = checksum
    
    def _add_to_history(self, file_path: str):
        """Add file to recent files history."""
        if file_path in self.file_history:
            self.file_history.remove(file_path)
        
        self.file_history.insert(0, file_path)
        
        # Keep only last 10 files
        self.file_history = self.file_history[:10]
    
    def get_recent_files(self) -> List[Dict[str, Any]]:
        """Get list of recently opened files."""
        recent_files = []
        
        for file_path in self.file_history:
            if Path(file_path).exists():
                try:
                    info = self.get_file_info(file_path)
                    recent_files.append(info)
                except:
                    pass  # Skip files that can't be read
        
        return recent_files
    
    def cleanup_workspace(self, older_than_days: int = 30):
        """Clean up old files in workspace."""
        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        cleaned_count = 0
        
        for file_path in self.workspace_dir.rglob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        # Create backup before cleanup
                        self.backup_manager.create_backup(str(file_path), "_cleanup")
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up {file_path}: {str(e)}")
        
        self.logger.info(f"Cleaned up {cleaned_count} old files")
        return cleaned_count
    
    def get_workspace_stats(self) -> Dict[str, Any]:
        """Get workspace statistics."""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "workflow_files": 0,
            "backup_files": 0,
            "oldest_file": None,
            "newest_file": None
        }
        
        oldest_time = float('inf')
        newest_time = 0
        
        for file_path in self.workspace_dir.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                stats["total_files"] += 1
                stats["total_size"] += stat.st_size
                
                if file_path.suffix == '.json':
                    stats["workflow_files"] += 1
                
                if stat.st_mtime < oldest_time:
                    oldest_time = stat.st_mtime
                    stats["oldest_file"] = {
                        "path": str(file_path),
                        "modified": datetime.fromtimestamp(stat.st_mtime)
                    }
                
                if stat.st_mtime > newest_time:
                    newest_time = stat.st_mtime
                    stats["newest_file"] = {
                        "path": str(file_path),
                        "modified": datetime.fromtimestamp(stat.st_mtime)
                    }
        
        # Get backup stats
        backup_files = self.backup_manager.list_backups()
        stats["backup_files"] = len(backup_files)
        
        return stats
