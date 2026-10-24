#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload Cleanup Utility

This module provides scheduled cleanup functionality for uploaded files
to prevent disk space accumulation on the server.
"""

import logging
import time
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def get_file_age_minutes(file_path: Path) -> float:
    """
    Get the age of a file in minutes.

    Args:
        file_path: Path to the file

    Returns:
        Age of the file in minutes
    """
    try:
        mtime = file_path.stat().st_mtime
        age_seconds = time.time() - mtime
        return age_seconds / 60.0
    except OSError:
        return 0


def get_file_size_mb(file_path: Path) -> float:
    """
    Get the size of a file in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        Size of the file in MB
    """
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0


def cleanup_directory(directory: Path, max_age_minutes: float, dry_run: bool = False) -> Tuple[int, float]:
    """
    Clean up files older than max_age_minutes from a directory.

    Args:
        directory: Path to the directory to clean
        max_age_minutes: Maximum age of files in minutes
        dry_run: If True, only log what would be deleted

    Returns:
        Tuple of (files_deleted_count, total_size_freed_mb)
    """
    if not directory.exists():
        logger.debug(f"Directory does not exist: {directory}")
        return 0, 0.0

    files_deleted = 0
    size_freed_mb = 0.0

    try:
        for file_path in directory.iterdir():
            # Skip directories and hidden files
            if file_path.is_dir() or file_path.name.startswith('.'):
                continue

            age_minutes = get_file_age_minutes(file_path)

            if age_minutes > max_age_minutes:
                file_size = get_file_size_mb(file_path)

                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would delete: {file_path.name} (age: {age_minutes:.1f}min, size: {file_size:.2f}MB)"
                    )
                else:
                    try:
                        file_path.unlink()
                        files_deleted += 1
                        size_freed_mb += file_size
                        logger.debug(f"Deleted: {file_path.name} (age: {age_minutes:.1f}min, size: {file_size:.2f}MB)")
                    except OSError as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

    except OSError as e:
        logger.error(f"Error accessing directory {directory}: {e}")

    return files_deleted, size_freed_mb


def cleanup_uploads(
    photos_dir: Path, texts_dir: Path, results_dir: Path, audio_dir: Path, max_age_minutes: float, dry_run: bool = False
) -> dict:
    """
    Clean up all upload directories.

    Args:
        photos_dir: Path to photos upload directory
        texts_dir: Path to texts upload directory
        results_dir: Path to results directory
        audio_dir: Path to TTS audio files directory
        max_age_minutes: Maximum age of files in minutes
        dry_run: If True, only log what would be deleted

    Returns:
        Dictionary with cleanup statistics
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting upload cleanup (max age: {max_age_minutes}min)")

    total_files = 0
    total_size_mb = 0.0

    directories = [
        ("photos", photos_dir),
        ("texts", texts_dir),
        ("results", results_dir),
        ("audio", audio_dir),  # Added TTS audio cleanup
    ]

    stats = {}

    for name, directory in directories:
        files_deleted, size_freed = cleanup_directory(directory, max_age_minutes, dry_run)
        stats[name] = {"files_deleted": files_deleted, "size_freed_mb": size_freed}
        total_files += files_deleted
        total_size_mb += size_freed

    stats["total"] = {"files_deleted": total_files, "size_freed_mb": total_size_mb}

    if total_files > 0:
        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Cleanup complete: "
            f"{total_files} files deleted, {total_size_mb:.2f}MB freed"
        )
    else:
        logger.debug("Cleanup complete: No files to delete")

    return stats


def scheduled_cleanup_job(app):
    """
    Scheduled job function that runs within Flask app context.

    Args:
        app: Flask application instance
    """
    from backend.config import settings

    with app.app_context():
        try:
            cleanup_uploads(
                photos_dir=settings.PHOTOS_DIR,
                texts_dir=settings.TEXTS_DIR,
                results_dir=settings.RESULTS_DIR,
                audio_dir=settings.AUDIO_DIR,  # Added TTS audio cleanup
                max_age_minutes=settings.FILE_MAX_AGE_MINUTES,
                dry_run=False,
            )
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")
