#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for TTS audio file cleanup functionality.

This script verifies that:
1. Old audio files are deleted after FILE_MAX_AGE_MINUTES
2. Recent audio files are preserved
3. Cleanup statistics are accurate
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from utils.cleanup import cleanup_directory, get_file_age_minutes


def create_test_audio_file(directory: Path, filename: str, age_minutes: float = 0):
    """
    Create a test audio file with specified age.

    Args:
        directory: Directory to create file in
        filename: Name of the file
        age_minutes: Age to set (in minutes before now)
    """
    filepath = directory / filename

    # Create file with some content
    filepath.write_text(f"Test audio content for {filename}")

    # Set file modification time to simulate age
    if age_minutes > 0:
        current_time = time.time()
        old_time = current_time - (age_minutes * 60)
        os.utime(filepath, (old_time, old_time))

    return filepath


def test_audio_cleanup():
    """Test the audio cleanup functionality."""
    print("=" * 70)
    print("TTS Audio Cleanup Test")
    print("=" * 70)
    print()

    # Configuration
    print(f"📁 Audio Directory: {settings.AUDIO_DIR}")
    print(f"⏰ Cleanup Interval: {settings.CLEANUP_INTERVAL_MINUTES} minutes")
    print(f"🗑️  Max File Age: {settings.FILE_MAX_AGE_MINUTES} minutes")
    print()

    # Create test files
    print("Creating test files...")
    test_files = [
        ("recent_audio_1.mp3", 5),  # 5 minutes old (should be kept)
        ("recent_audio_2.mp3", 30),  # 30 minutes old (should be kept)
        ("old_audio_1.mp3", 65),  # 65 minutes old (should be deleted)
        ("old_audio_2.mp3", 120),  # 120 minutes old (should be deleted)
        ("old_audio_3.mp3", 180),  # 180 minutes old (should be deleted)
    ]

    created_files = []
    for filename, age in test_files:
        filepath = create_test_audio_file(settings.AUDIO_DIR, filename, age)
        created_files.append(filepath)
        file_age = get_file_age_minutes(filepath)
        status = "🟢 KEEP" if age < settings.FILE_MAX_AGE_MINUTES else "🔴 DELETE"
        print(f"  {status} {filename:25s} (age: {file_age:.1f} min)")

    print()

    # Run cleanup in dry-run mode first
    print("🔍 Running DRY RUN cleanup...")
    files_deleted_dry, size_freed_dry = cleanup_directory(
        settings.AUDIO_DIR, settings.FILE_MAX_AGE_MINUTES, dry_run=True
    )
    print(f"   Would delete: {files_deleted_dry} files")
    print()

    # Run actual cleanup
    print("🗑️  Running ACTUAL cleanup...")
    files_deleted, size_freed = cleanup_directory(settings.AUDIO_DIR, settings.FILE_MAX_AGE_MINUTES, dry_run=False)
    print(f"   ✅ Deleted: {files_deleted} files")
    print(f"   💾 Freed: {size_freed:.4f} MB")
    print()

    # Verify results
    print("✅ Verification:")
    remaining_files = list(settings.AUDIO_DIR.glob("*.mp3"))
    for filepath in created_files:
        if filepath.exists():
            age = get_file_age_minutes(filepath)
            print(f"  ✅ Kept: {filepath.name} (age: {age:.1f} min)")
        else:
            print(f"  🗑️  Deleted: {filepath.name}")

    print()
    print("=" * 70)

    # Cleanup test files
    print("\n🧹 Cleaning up test files...")
    for filepath in remaining_files:
        if filepath.name.startswith(("recent_audio", "old_audio")):
            filepath.unlink()
            print(f"   Removed: {filepath.name}")

    print("\n✅ Test complete!")
    print()

    # Summary
    expected_deleted = sum(1 for _, age in test_files if age > settings.FILE_MAX_AGE_MINUTES)
    expected_kept = sum(1 for _, age in test_files if age <= settings.FILE_MAX_AGE_MINUTES)

    print("📊 Summary:")
    print(f"   Files created: {len(test_files)}")
    print(f"   Expected to delete: {expected_deleted}")
    print(f"   Expected to keep: {expected_kept}")
    print(f"   Actually deleted: {files_deleted}")
    print()

    if files_deleted == expected_deleted:
        print("✅ TEST PASSED! Cleanup working correctly.")
        return True
    else:
        print("❌ TEST FAILED! Cleanup behavior unexpected.")
        return False


if __name__ == "__main__":
    try:
        success = test_audio_cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
