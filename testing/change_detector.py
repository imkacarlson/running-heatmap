#!/usr/bin/env python3
"""
Change detection infrastructure for test optimization.
Tracks file modifications to skip expensive operations when unchanged.
"""

import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChangeType(Enum):
    """Types of changes that can be detected."""
    SOURCE = "source"
    DATA = "data"
    CONFIG = "config"
    UNKNOWN = "unknown"


@dataclass
class ChangeReport:
    """Report of detected changes and optimization recommendations."""
    has_changes: bool
    changed_files: List[Path]
    change_type: ChangeType
    baseline_time: datetime
    skip_build: bool
    skip_data: bool


@dataclass
class BuildOptimization:
    """Build optimization recommendations."""
    apk_exists: bool
    source_unchanged: bool
    data_unchanged: bool
    can_skip_build: bool
    can_skip_data: bool


class ChangeDetector:
    """
    Intelligent change detection for test optimization.
    Monitors source files and data files to determine when expensive operations can be skipped.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize change detector with project root path."""
        if project_root is None:
            # Default to testing directory parent (project root)
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.testing_root = self.project_root / "testing"
        self.cache_dir = self.testing_root / ".change_detector_cache"
        self.baseline_file = self.cache_dir / "baseline.json"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        
        # Define paths to monitor
        self.source_paths = [
            self.project_root / "server",
            self.project_root / "mobile",
            self.project_root / "package.json",
        ]
        
        self.data_paths = [
            self.testing_root / "test_data",
            self.project_root / "data" / "raw",
        ]
        
        self.config_paths = [
            self.testing_root / "conftest.py",
            self.testing_root / "config.py",
            self.testing_root / "pytest.ini",
        ]
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """Get file modification time and size."""
        try:
            stat = file_path.stat()
            return {
                "mtime": stat.st_mtime,
                "size": stat.st_size,
                "exists": True
            }
        except (OSError, FileNotFoundError):
            return {
                "mtime": 0,
                "size": 0, 
                "exists": False
            }
    
    def _scan_directory(self, directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, Dict]:
        """Recursively scan directory for file information."""
        if not directory.exists():
            return {}
        
        file_info = {}
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    # Filter by extensions if specified
                    if extensions and file_path.suffix.lower() not in extensions:
                        continue
                    
                    # Skip cache and build directories
                    if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'build', 'dist'] 
                           for part in file_path.parts):
                        continue
                    
                    relative_path = str(file_path.relative_to(self.project_root))
                    file_info[relative_path] = self._get_file_info(file_path)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not scan directory {directory}: {e}")
        
        return file_info
    
    def _get_current_baseline(self) -> Dict:
        """Get current file baseline for all monitored paths."""
        baseline = {
            "timestamp": time.time(),
            "source_files": {},
            "data_files": {},
            "config_files": {}
        }
        
        # Scan source directories
        for path in self.source_paths:
            if path.is_dir():
                # Focus on source code extensions for source directories
                extensions = ['.py', '.js', '.html', '.css', '.java', '.xml', '.json']
                baseline["source_files"].update(self._scan_directory(path, extensions))
            elif path.is_file():
                relative_path = str(path.relative_to(self.project_root))
                baseline["source_files"][relative_path] = self._get_file_info(path)
        
        # Scan data directories  
        for path in self.data_paths:
            if path.is_dir():
                # Focus on data file extensions
                extensions = ['.gpx', '.pkl', '.pmtiles', '.json', '.geojson']
                baseline["data_files"].update(self._scan_directory(path, extensions))
            elif path.is_file():
                relative_path = str(path.relative_to(self.project_root))
                baseline["data_files"][relative_path] = self._get_file_info(path)
        
        # Scan config files
        for path in self.config_paths:
            if path.exists():
                relative_path = str(path.relative_to(self.project_root))
                baseline["config_files"][relative_path] = self._get_file_info(path)
        
        return baseline
    
    def _load_baseline(self) -> Optional[Dict]:
        """Load previous baseline from cache."""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load baseline: {e}")
        return None
    
    def _save_baseline(self, baseline: Dict):
        """Save baseline to cache."""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save baseline: {e}")
    
    def _compare_baselines(self, old_baseline: Dict, new_baseline: Dict) -> Tuple[List[str], ChangeType]:
        """Compare baselines and return changed files and change type."""
        changed_files = []
        change_types = set()
        
        # Check each category
        for category in ["source_files", "data_files", "config_files"]:
            old_files = old_baseline.get(category, {})
            new_files = new_baseline.get(category, {})
            
            # Find changed, added, or removed files
            all_files = set(old_files.keys()) | set(new_files.keys())
            
            for file_path in all_files:
                old_info = old_files.get(file_path, {"exists": False})
                new_info = new_files.get(file_path, {"exists": False})
                
                # Check if file changed
                if (old_info.get("exists") != new_info.get("exists") or
                    old_info.get("mtime", 0) != new_info.get("mtime", 0) or
                    old_info.get("size", 0) != new_info.get("size", 0)):
                    
                    changed_files.append(file_path)
                    
                    if category == "source_files":
                        change_types.add(ChangeType.SOURCE)
                    elif category == "data_files":
                        change_types.add(ChangeType.DATA)
                    elif category == "config_files":
                        change_types.add(ChangeType.CONFIG)
        
        # Determine primary change type
        if ChangeType.SOURCE in change_types:
            primary_change_type = ChangeType.SOURCE
        elif ChangeType.DATA in change_types:
            primary_change_type = ChangeType.DATA
        elif ChangeType.CONFIG in change_types:
            primary_change_type = ChangeType.CONFIG
        else:
            primary_change_type = ChangeType.UNKNOWN
        
        return changed_files, primary_change_type
    
    def has_source_changed(self) -> bool:
        """Check if source code files have changed since last baseline."""
        try:
            old_baseline = self._load_baseline()
            if not old_baseline:
                return True  # No baseline means assume changes
            
            new_baseline = self._get_current_baseline()
            changed_files, change_type = self._compare_baselines(old_baseline, new_baseline)
            
            # Return True if any source files changed
            return change_type == ChangeType.SOURCE or any(
                file_path in new_baseline.get("source_files", {}) 
                for file_path in changed_files
            )
        except Exception as e:
            print(f"Warning: Source change detection failed: {e}")
            return True  # Assume changes on error
    
    def has_data_changed(self) -> bool:
        """Check if data files have changed since last baseline."""
        try:
            old_baseline = self._load_baseline()
            if not old_baseline:
                return True  # No baseline means assume changes
            
            new_baseline = self._get_current_baseline()
            changed_files, change_type = self._compare_baselines(old_baseline, new_baseline)
            
            # Return True if any data files changed
            return change_type == ChangeType.DATA or any(
                file_path in new_baseline.get("data_files", {})
                for file_path in changed_files
            )
        except Exception as e:
            print(f"Warning: Data change detection failed: {e}")
            return True  # Assume changes on error
    
    def get_change_report(self) -> ChangeReport:
        """Get comprehensive change report with optimization recommendations."""
        try:
            old_baseline = self._load_baseline()
            new_baseline = self._get_current_baseline()
            
            if not old_baseline:
                # No baseline - assume all changes
                return ChangeReport(
                    has_changes=True,
                    changed_files=[],
                    change_type=ChangeType.UNKNOWN,
                    baseline_time=datetime.now(),
                    skip_build=False,
                    skip_data=False
                )
            
            changed_files, change_type = self._compare_baselines(old_baseline, new_baseline)
            
            # Convert file paths to Path objects
            changed_paths = [Path(self.project_root / file_path) for file_path in changed_files]
            
            # Determine optimization recommendations
            source_changed = any(
                file_path in new_baseline.get("source_files", {})
                for file_path in changed_files
            )
            data_changed = any(
                file_path in new_baseline.get("data_files", {})
                for file_path in changed_files
            )
            
            return ChangeReport(
                has_changes=bool(changed_files),
                changed_files=changed_paths,
                change_type=change_type,
                baseline_time=datetime.fromtimestamp(old_baseline.get("timestamp", 0)),
                skip_build=not source_changed,
                skip_data=not data_changed
            )
        except Exception as e:
            print(f"Warning: Change report generation failed: {e}")
            # Return safe defaults on error
            return ChangeReport(
                has_changes=True,
                changed_files=[],
                change_type=ChangeType.UNKNOWN,
                baseline_time=datetime.now(),
                skip_build=False,
                skip_data=False
            )
    
    def should_rebuild_apk(self) -> bool:
        """Determine if APK should be rebuilt based on source changes and APK existence."""
        try:
            # Check if cached APK exists
            cached_apk_path = self.testing_root / "cached_test_apk" / "app-debug.apk"
            apk_exists = cached_apk_path.exists()
            
            if not apk_exists:
                return True  # No cached APK, must build
            
            # Check if source files changed
            source_changed = self.has_source_changed()
            
            return source_changed
        except Exception as e:
            print(f"Warning: APK rebuild check failed: {e}")
            return True  # Rebuild on error to be safe
    
    def should_reprocess_data(self) -> bool:
        """Determine if data should be reprocessed based on data changes and PMTiles existence.""" 
        try:
            # Check if cached PMTiles exists
            cached_pmtiles_path = self.testing_root / "cached_test_data" / "runs.pmtiles"
            pmtiles_exists = cached_pmtiles_path.exists()
            
            if not pmtiles_exists:
                return True  # No cached data, must process
            
            # Check if data files changed
            data_changed = self.has_data_changed()
            
            return data_changed
        except Exception as e:
            print(f"Warning: Data reprocessing check failed: {e}")
            return True  # Reprocess on error to be safe
    
    def get_build_optimization(self) -> BuildOptimization:
        """Get comprehensive build optimization recommendations."""
        try:
            # Check cached artifacts existence
            cached_apk_path = self.testing_root / "cached_test_apk" / "app-debug.apk"
            cached_pmtiles_path = self.testing_root / "cached_test_data" / "runs.pmtiles"
            
            apk_exists = cached_apk_path.exists()
            pmtiles_exists = cached_pmtiles_path.exists()
            
            # Check for changes
            source_changed = self.has_source_changed()
            data_changed = self.has_data_changed()
            
            return BuildOptimization(
                apk_exists=apk_exists,
                source_unchanged=not source_changed,
                data_unchanged=not data_changed,
                can_skip_build=apk_exists and not source_changed,
                can_skip_data=pmtiles_exists and not data_changed
            )
        except Exception as e:
            print(f"Warning: Build optimization check failed: {e}")
            # Return safe defaults on error
            return BuildOptimization(
                apk_exists=False,
                source_unchanged=False,
                data_unchanged=False,
                can_skip_build=False,
                can_skip_data=False
            )
    
    def update_baseline(self):
        """Update the baseline with current file states."""
        try:
            new_baseline = self._get_current_baseline()
            self._save_baseline(new_baseline)
            print(f"✅ Change detection baseline updated")
        except Exception as e:
            print(f"Warning: Could not update baseline: {e}")
    
    def reset_baseline(self):
        """Reset the baseline cache (force full rebuild on next run)."""
        try:
            if self.baseline_file.exists():
                self.baseline_file.unlink()
                print("✅ Change detection baseline reset")
        except Exception as e:
            print(f"Warning: Could not reset baseline: {e}")


def main():
    """Command line interface for change detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Change detection for test optimization")
    parser.add_argument("--check-source", action="store_true", help="Check if source files changed")
    parser.add_argument("--check-data", action="store_true", help="Check if data files changed")
    parser.add_argument("--should-rebuild-apk", action="store_true", help="Check if APK should be rebuilt")
    parser.add_argument("--should-reprocess-data", action="store_true", help="Check if data should be reprocessed")
    parser.add_argument("--report", action="store_true", help="Generate full change report")
    parser.add_argument("--update-baseline", action="store_true", help="Update baseline with current state")
    parser.add_argument("--reset-baseline", action="store_true", help="Reset baseline cache")
    
    args = parser.parse_args()
    
    detector = ChangeDetector()
    
    if args.check_source:
        result = detector.has_source_changed()
        print(f"Source changed: {result}")
        return result
    
    if args.check_data:
        result = detector.has_data_changed()
        print(f"Data changed: {result}")
        return result
    
    if args.should_rebuild_apk:
        result = detector.should_rebuild_apk()
        print(f"Should rebuild APK: {result}")
        return result
    
    if args.should_reprocess_data:
        result = detector.should_reprocess_data()
        print(f"Should reprocess data: {result}")
        return result
    
    if args.report:
        report = detector.get_change_report()
        print(f"Change Report:")
        print(f"  Has changes: {report.has_changes}")
        print(f"  Change type: {report.change_type.value}")
        print(f"  Changed files: {len(report.changed_files)}")
        print(f"  Skip build: {report.skip_build}")
        print(f"  Skip data: {report.skip_data}")
        if report.changed_files:
            print(f"  Files:")
            for file_path in report.changed_files[:10]:  # Show first 10
                print(f"    - {file_path}")
            if len(report.changed_files) > 10:
                print(f"    ... and {len(report.changed_files) - 10} more")
        return not report.has_changes
    
    if args.update_baseline:
        detector.update_baseline()
        return True
    
    if args.reset_baseline:
        detector.reset_baseline()
        return True
    
    # Default: show optimization recommendations
    optimization = detector.get_build_optimization()
    print(f"Build Optimization Recommendations:")
    print(f"  APK exists: {optimization.apk_exists}")
    print(f"  Source unchanged: {optimization.source_unchanged}")
    print(f"  Data unchanged: {optimization.data_unchanged}")
    print(f"  Can skip build: {optimization.can_skip_build}")
    print(f"  Can skip data: {optimization.can_skip_data}")
    
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)