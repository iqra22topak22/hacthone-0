# filesystem_watcher.py  (Improved version with better timestamp)
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import logging

# Better logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class InboxHandler(FileSystemEventHandler):
    def __init__(self, vault_path: Path):
        self.needs_action = vault_path / "Needs_Action"
        self.inbox = vault_path / "Inbox"

    def on_created(self, event):
        if event.is_directory:
            return
        
        source = Path(event.src_path)
        # Only process common file types
        if source.suffix.lower() in ['.txt', '.md', '.pdf', '.jpg', '.png', '.docx']:
            # Use proper ISO timestamp for reliability
            now = time.strftime("%Y-%m-%d_%H-%M-%S")
            dest_name = f"FILE_{source.stem}_{now}{source.suffix}.md"  # better naming
            
            dest = self.needs_action / dest_name

            # Create clean markdown wrapper with clear timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S PKT")
            content = f"""---
type: file_drop
original_name: {source.name}
original_path: {source}
detected_at: {timestamp}
file_size: {source.stat().st_size} bytes
---

## Dropped File Info
- **File dropped in Inbox** at: {timestamp}
- Original name: {source.name}
- Copied to: {dest_name}

Now waiting for AI Employee to process this file.
"""

            try:
                dest.write_text(content, encoding='utf-8')
                logging.info(f"File wrapped successfully: {source.name} → {dest_name}")
            except Exception as e:
                logging.error(f"Failed to write wrapper: {e}")

if __name__ == "__main__":
    vault = Path.cwd()
    inbox_path = vault / "Inbox"
    
    if not inbox_path.exists():
        print("Inbox folder not found! Make sure you're in the vault root.")
        exit(1)

    event_handler = InboxHandler(vault)
    observer = Observer()
    observer.schedule(event_handler, str(inbox_path), recursive=False)
    observer.start()

    print("🔍 Filesystem Watcher started... Drop files in /Inbox to test")
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Watcher stopped.")
    observer.join()