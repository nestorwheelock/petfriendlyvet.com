#!/usr/bin/env python3
"""
Media Optimization Script for Django Sites
Uses NVIDIA GPU for video encoding, Pillow for images.

Usage:
    python optimize_media.py [options]

Options:
    --all           Process all media files (default: only new/unoptimized)
    --dry-run       Show what would be done without making changes
    --images-only   Only process images
    --videos-only   Only process videos
    --path PATH     Specific path to process (default: media/)
    --no-backup     Skip creating backups of originals
"""

import os
import sys
import argparse
import hashlib
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional imports - gracefully handle missing dependencies
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Image optimization disabled.")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False
    print("Warning: pillow-heif not installed. HEIC conversion disabled.")

# Configuration (loaded from deploy.conf or defaults)
CONFIG = {
    'IMAGE_MAX_WIDTH': 1920,
    'IMAGE_QUALITY': 85,
    'THUMB_WIDTH': 400,
    'THUMB_QUALITY': 80,
    'VIDEO_MAX_HEIGHT': 1080,
    'VIDEO_CRF': 28,
    'USE_NVENC': True,
}

# File extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic', '.heif'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
OPTIMIZED_MARKER = '.optimized'


class MediaOptimizer:
    def __init__(self, media_path, config=None, dry_run=False, backup=True):
        self.media_path = Path(media_path)
        self.config = config or CONFIG
        self.dry_run = dry_run
        self.backup = backup
        self.backup_dir = Path.home() / '.media_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')

        self.stats = {
            'images_processed': 0,
            'images_skipped': 0,
            'videos_processed': 0,
            'videos_skipped': 0,
            'bytes_saved': 0,
            'errors': [],
            'duplicates_found': 0,
        }

        self.seen_hashes = {}

    def log(self, message, level='INFO'):
        colors = {
            'INFO': '\033[0;34m',
            'SUCCESS': '\033[0;32m',
            'WARNING': '\033[1;33m',
            'ERROR': '\033[0;31m',
        }
        nc = '\033[0m'
        print(f"{colors.get(level, '')}{level}{nc}: {message}")

    def is_optimized(self, filepath):
        """Check if file has already been optimized."""
        marker_file = filepath.with_suffix(filepath.suffix + OPTIMIZED_MARKER)
        return marker_file.exists()

    def mark_optimized(self, filepath):
        """Mark file as optimized."""
        marker_file = filepath.with_suffix(filepath.suffix + OPTIMIZED_MARKER)
        marker_file.touch()

    def get_file_hash(self, filepath, chunk_size=65536):
        """Get MD5 hash of file for duplicate detection."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def backup_file(self, filepath):
        """Create backup of original file."""
        if not self.backup or self.dry_run:
            return

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        rel_path = filepath.relative_to(self.media_path)
        backup_path = self.backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)

    def optimize_image(self, filepath):
        """Optimize a single image file."""
        if not HAS_PIL:
            return False

        filepath = Path(filepath)

        # Skip if already optimized
        if self.is_optimized(filepath):
            self.stats['images_skipped'] += 1
            return False

        # Check for duplicates
        file_hash = self.get_file_hash(filepath)
        if file_hash in self.seen_hashes:
            self.log(f"Duplicate found: {filepath} == {self.seen_hashes[file_hash]}", 'WARNING')
            self.stats['duplicates_found'] += 1
            return False
        self.seen_hashes[file_hash] = filepath

        original_size = filepath.stat().st_size

        if self.dry_run:
            self.log(f"Would optimize: {filepath} ({original_size / 1024:.1f}KB)")
            return True

        try:
            self.backup_file(filepath)

            with Image.open(filepath) as img:
                # Convert RGBA to RGB for WebP (if not transparent)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # Keep alpha for images that need it
                    pass
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if larger than max width
                if img.width > self.config['IMAGE_MAX_WIDTH']:
                    ratio = self.config['IMAGE_MAX_WIDTH'] / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize(
                        (self.config['IMAGE_MAX_WIDTH'], new_height),
                        Image.Resampling.LANCZOS
                    )

                # Determine output path (convert to WebP)
                output_path = filepath.with_suffix('.webp')

                # Save optimized version
                img.save(
                    output_path,
                    'WEBP',
                    quality=self.config['IMAGE_QUALITY'],
                    method=6  # Best compression
                )

                # Generate thumbnail
                self.generate_thumbnail(img, filepath)

                # Remove original if different extension
                if output_path != filepath:
                    filepath.unlink()

                new_size = output_path.stat().st_size
                saved = original_size - new_size
                self.stats['bytes_saved'] += saved
                self.stats['images_processed'] += 1

                self.mark_optimized(output_path)
                self.log(f"Optimized: {filepath.name} → {output_path.name} "
                        f"({original_size/1024:.1f}KB → {new_size/1024:.1f}KB, "
                        f"saved {saved/1024:.1f}KB)", 'SUCCESS')

                return True

        except Exception as e:
            self.stats['errors'].append((filepath, str(e)))
            self.log(f"Error optimizing {filepath}: {e}", 'ERROR')
            return False

    def generate_thumbnail(self, img, original_path):
        """Generate thumbnail for image."""
        thumb_path = original_path.parent / 'thumbs' / (original_path.stem + '_thumb.webp')
        thumb_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate thumbnail size
        ratio = self.config['THUMB_WIDTH'] / img.width
        thumb_height = int(img.height * ratio)

        thumb = img.resize(
            (self.config['THUMB_WIDTH'], thumb_height),
            Image.Resampling.LANCZOS
        )

        thumb.save(
            thumb_path,
            'WEBP',
            quality=self.config['THUMB_QUALITY']
        )

    def check_nvenc_available(self):
        """Check if NVIDIA NVENC is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True
            )
            return 'hevc_nvenc' in result.stdout or 'h264_nvenc' in result.stdout
        except FileNotFoundError:
            return False

    def optimize_video(self, filepath):
        """Optimize a single video file using ffmpeg."""
        filepath = Path(filepath)

        # Skip if already optimized
        if self.is_optimized(filepath):
            self.stats['videos_skipped'] += 1
            return False

        original_size = filepath.stat().st_size

        if self.dry_run:
            self.log(f"Would optimize video: {filepath} ({original_size / 1024 / 1024:.1f}MB)")
            return True

        try:
            self.backup_file(filepath)

            output_path = filepath.with_suffix('.mp4')
            temp_output = filepath.with_suffix('.temp.mp4')

            # Build ffmpeg command
            use_nvenc = self.config['USE_NVENC'] and self.check_nvenc_available()

            if use_nvenc:
                encoder = 'hevc_nvenc'
                codec_opts = [
                    '-c:v', encoder,
                    '-preset', 'p4',  # Medium quality/speed
                    '-cq', str(self.config['VIDEO_CRF']),
                ]
            else:
                encoder = 'libx265'
                codec_opts = [
                    '-c:v', encoder,
                    '-preset', 'medium',
                    '-crf', str(self.config['VIDEO_CRF']),
                ]

            cmd = [
                'ffmpeg', '-i', str(filepath),
                '-vf', f"scale=-2:'min({self.config['VIDEO_MAX_HEIGHT']},ih)'",
                *codec_opts,
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                str(temp_output)
            ]

            self.log(f"Encoding video: {filepath.name} using {encoder}...")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"ffmpeg error: {result.stderr[-500:]}")

            # Replace original with optimized
            if temp_output.exists():
                if filepath != output_path:
                    filepath.unlink()
                temp_output.rename(output_path)

                new_size = output_path.stat().st_size
                saved = original_size - new_size
                self.stats['bytes_saved'] += saved
                self.stats['videos_processed'] += 1

                self.mark_optimized(output_path)
                self.log(f"Optimized video: {filepath.name} → {output_path.name} "
                        f"({original_size/1024/1024:.1f}MB → {new_size/1024/1024:.1f}MB, "
                        f"saved {saved/1024/1024:.1f}MB)", 'SUCCESS')

                return True

        except Exception as e:
            self.stats['errors'].append((filepath, str(e)))
            self.log(f"Error optimizing video {filepath}: {e}", 'ERROR')
            # Clean up temp file
            temp_output = filepath.with_suffix('.temp.mp4')
            if temp_output.exists():
                temp_output.unlink()
            return False

        return False

    def find_media_files(self, images_only=False, videos_only=False):
        """Find all media files in the media directory."""
        files = {'images': [], 'videos': []}

        for filepath in self.media_path.rglob('*'):
            if not filepath.is_file():
                continue

            # Skip marker files and temp files
            if filepath.suffix == OPTIMIZED_MARKER or '.temp.' in filepath.name:
                continue

            # Skip thumbs directory
            if 'thumbs' in filepath.parts:
                continue

            suffix = filepath.suffix.lower()

            if not videos_only and suffix in IMAGE_EXTENSIONS:
                files['images'].append(filepath)
            elif not images_only and suffix in VIDEO_EXTENSIONS:
                files['videos'].append(filepath)

        return files

    def run(self, images_only=False, videos_only=False, process_all=False):
        """Run the optimization process."""
        self.log(f"Scanning {self.media_path} for media files...")

        files = self.find_media_files(images_only, videos_only)

        total_images = len(files['images'])
        total_videos = len(files['videos'])

        self.log(f"Found {total_images} images and {total_videos} videos")

        # Process images in parallel
        if files['images']:
            self.log(f"Processing {total_images} images...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self.optimize_image, f): f for f in files['images']}
                for i, future in enumerate(as_completed(futures), 1):
                    filepath = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"Error: {filepath}: {e}", 'ERROR')

                    # Progress indicator
                    if i % 100 == 0:
                        self.log(f"Progress: {i}/{total_images} images processed")

        # Process videos sequentially (GPU bound)
        if files['videos']:
            self.log(f"Processing {total_videos} videos...")
            for i, filepath in enumerate(files['videos'], 1):
                self.optimize_video(filepath)
                self.log(f"Progress: {i}/{total_videos} videos processed")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print optimization summary."""
        print("\n" + "=" * 60)
        print("OPTIMIZATION SUMMARY")
        print("=" * 60)
        print(f"Images processed:  {self.stats['images_processed']}")
        print(f"Images skipped:    {self.stats['images_skipped']}")
        print(f"Videos processed:  {self.stats['videos_processed']}")
        print(f"Videos skipped:    {self.stats['videos_skipped']}")
        print(f"Duplicates found:  {self.stats['duplicates_found']}")
        print(f"Total space saved: {self.stats['bytes_saved'] / 1024 / 1024:.2f} MB")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for filepath, error in self.stats['errors'][:10]:
                print(f"  - {filepath}: {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print("=" * 60)


def load_config(config_path=None):
    """Load configuration from deploy.conf."""
    if config_path is None:
        script_dir = Path(__file__).parent
        config_path = script_dir / 'deploy.conf'

    config = CONFIG.copy()

    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in config:
                    if key == 'USE_NVENC':
                        config[key] = value.lower() == 'true'
                    else:
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Optimize media files for web deployment'
    )
    parser.add_argument('--all', action='store_true',
                       help='Process all files, not just unoptimized ones')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--images-only', action='store_true',
                       help='Only process images')
    parser.add_argument('--videos-only', action='store_true',
                       help='Only process videos')
    parser.add_argument('--path', type=str, default=None,
                       help='Specific path to process (default: media/)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backups of originals')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file')

    args = parser.parse_args()

    # Determine media path
    if args.path:
        media_path = Path(args.path)
    else:
        # Default: look for media/ in current directory or project root
        script_dir = Path(__file__).parent
        project_dir = script_dir.parent
        media_path = project_dir / 'media'

        if not media_path.exists():
            # Try current directory
            media_path = Path.cwd() / 'media'

    if not media_path.exists():
        print(f"Error: Media directory not found: {media_path}")
        sys.exit(1)

    # Load configuration
    config = load_config(args.config)

    # Check dependencies
    if not HAS_PIL:
        print("Error: Pillow is required. Install with: pip install pillow pillow-heif")
        sys.exit(1)

    # Run optimizer
    optimizer = MediaOptimizer(
        media_path=media_path,
        config=config,
        dry_run=args.dry_run,
        backup=not args.no_backup
    )

    optimizer.run(
        images_only=args.images_only,
        videos_only=args.videos_only,
        process_all=args.all
    )


if __name__ == '__main__':
    main()
