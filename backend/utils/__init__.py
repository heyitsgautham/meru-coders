#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Scripts Package

Contains data management, benchmarking, TTS utilities, and file processing
for the Sanskrit Meter Identification System.
"""

from .file_processor import FileProcessor, FileProcessingError

__all__ = ['FileProcessor', 'FileProcessingError']
