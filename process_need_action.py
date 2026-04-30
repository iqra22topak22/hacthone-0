# process_need_action.py
import time
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

VAULT = Path.cwd()
NEEDS_ACTION = VAULT / "Needs_Action"
DONE = VAULT / "Done"

def process_files():
    files = list(NEEDS_ACTION.glob("FILE_*.md"))
    if not files:
        logging.info("No new files in Needs_Action right now.")
        return

    for file_path in files:
        logging.info(f"Found file to process: {file_path.name}")
        # Yahan future mein Claude ko call karenge
        # Abhi sirf move kar dete hain test ke liye
        try:
            new_path = DONE / file_path.name
            file_path.rename(new_path)
            logging.info(f"Moved to Done: {file_path.name}")
        except Exception as e:
            logging.error(f"Error moving file {file_path.name}: {e}")

if __name__ == "__main__":
    logging.info("Starting Needs_Action processor (every 30 seconds)")
    while True:
        try:
            process_files()
        except Exception as e:
            logging.error(f"Processor loop error: {e}")
        time.sleep(30)