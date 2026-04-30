# vault_loop.py - Continuous loop for processing Needs_Action files
import time
from pathlib import Path
from datetime import datetime
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

VAULT = Path.cwd()
NEEDS_ACTION = VAULT / "Needs_Action"
PLANS = VAULT / "Plans"
DONE = VAULT / "Done"
DASHBOARD = VAULT / "Dashboard.md"

def extract_original_name(content: str, filename: str) -> str:
    """Extract original_name from frontmatter or clean filename"""
    # Try frontmatter first
    match = re.search(r'original_name:\s*(.+)', content)
    if match:
        return match.group(1).strip()
    
    # Clean filename: remove FILE_ prefix and timestamp suffix
    clean = re.sub(r'^FILE_', '', filename)
    clean = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.md$', '', clean)
    return clean.replace('_', ' ')

def create_summary(content: str) -> str:
    """Create 2-3 sentence summary of file content"""
    # Remove frontmatter
    body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    body = body.strip()
    
    # Get first few lines as summary
    lines = body.split('\n')
    summary_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            summary_lines.append(line)
        if len(summary_lines) >= 3:
            break
    
    summary = ' '.join(summary_lines)[:300]
    if len(summary) > 250:
        summary = summary[:247] + '...'
    
    return summary if summary else "File contains metadata but no clear content body."

def check_money_mentioned(content: str) -> bool:
    """Check if money/payment is mentioned"""
    money_keywords = ['payment', 'pay', 'invoice', 'bill', 'cost', 'price', '$', 'USD', 'PKR', 'rupees', 'amount']
    return any(kw in content.lower() for kw in money_keywords)

def process_file(file_path: Path) -> bool:
    """Process a single file from Needs_Action"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logging.error(f"Error reading {file_path.name}: {e}")
        return False

    original_name = extract_original_name(content, file_path.name)
    summary = create_summary(content)
    has_money = check_money_mentioned(content)
    
    now = datetime.now()
    plan_name = f"PLAN_{original_name.replace(' ', '_')}_{now.strftime('%Y-%m-%d_%H-%M')}.md"
    plan_path = PLANS / plan_name
    
    # Create plan file
    plan_content = f"""---
created: {now.strftime('%Y-%m-%d %H:%M:%S')}
from_file: {file_path.name}
original_name: {original_name}
---
## Summary
{summary}

## Next Actions
- [ ] Read full original file if needed
- [ ] Suggest reply / action based on content
- [ ] If money/payment mentioned, add approval note
"""
    if has_money:
        plan_content += "\n**NOTE:** Payment/money mentioned - requires approval workflow.\n"
    
    try:
        plan_path.write_text(plan_content, encoding='utf-8')
        logging.info(f"Plan created: {plan_name}")
    except Exception as e:
        logging.error(f"Error creating plan file: {e}")
        return False
    
    # Update Dashboard
    dashboard_line = f"\n- [{now.strftime('%Y-%m-%d %H:%M:%S')}] Processed drop: {original_name} (Plan created)"
    try:
        with open(DASHBOARD, 'a', encoding='utf-8') as f:
            f.write(dashboard_line)
        logging.info("Dashboard updated")
    except Exception as e:
        logging.error(f"Error updating Dashboard: {e}")
    
    # Move to Done
    dest = DONE / file_path.name
    try:
        file_path.rename(dest)
        logging.info(f"Moved to Done: {file_path.name}")
    except Exception as e:
        logging.error(f"Error moving file to Done: {e}")
        return False
    
    return True

def main():
    logging.info("=" * 50)
    logging.info("Vault Loop Started - Scanning every 45 seconds")
    logging.info("=" * 50)
    
    iteration = 0
    while True:
        iteration += 1
        logging.info(f"\n--- Iteration {iteration} ---")
        
        files = sorted(NEEDS_ACTION.glob("FILE_*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        
        if files:
            logging.info(f"Found {len(files)} file(s) to process")
            for f in files:
                process_file(f)
        else:
            logging.info("No new files in Needs_Action - waiting...")
        
        time.sleep(45)

if __name__ == "__main__":
    # Verify folders exist
    for folder in [NEEDS_ACTION, PLANS, DONE]:
        if not folder.exists():
            logging.error(f"Folder not found: {folder}")
            exit(1)
    
    if not DASHBOARD.exists():
        logging.error(f"Dashboard.md not found: {DASHBOARD}")
        exit(1)
    
    main()
