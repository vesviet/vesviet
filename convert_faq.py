import os, glob, re
from datetime import datetime, timezone, timedelta

# Create an exact timezone for +07:00 to match the previous lastmods
tz = timezone(timedelta(hours=7))
current_date = datetime.now(tz).replace(microsecond=0).isoformat()

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    match = re.search(r'^(#{2,3})\s+FAQ\s*$', content, re.MULTILINE)
    if not match:
        return False
        
    faq_start_idx = match.end()
    
    # Look for the next header of the same or higher level as the FAQ header
    # e.g., if FAQ is ##, look for ## or #. If FAQ is ###, look for ###, ## or #
    faq_level = len(match.group(1))
    next_header_pattern = re.compile(r'^#{1,' + str(faq_level) + r'}\s+(?!FAQ).*$', re.MULTILINE)
    
    next_header_match = next_header_pattern.search(content[faq_start_idx:])
    faq_end_idx = faq_start_idx + next_header_match.start() if next_header_match else len(content)

    faq_section = content[faq_start_idx:faq_end_idx]
    
    # Split by any header deeper than the FAQ header
    question_pattern = re.compile(r'^(#{' + str(faq_level + 1) + r',})\s+(.+)$', re.MULTILINE)
    parts = question_pattern.split(faq_section)
    
    if len(parts) <= 1:
        return False
        
    new_faq_section = parts[0]
    if not new_faq_section.endswith('\n'):
        new_faq_section += '\n'
    
    i = 1
    while i < len(parts):
        hashes = parts[i]
        question = parts[i+1].strip()
        answer = parts[i+2].strip()
        
        # Escape quotes in the question string if any
        question = question.replace('"', '\\"')
        
        new_faq_section += f'\n{{{{< faq q="{question}" >}}}}\n{answer}\n{{{{< /faq >}}}}\n'
        
        i += 3
        
    if not new_faq_section.endswith('\n'):
        new_faq_section += '\n'
        
    new_content = content[:faq_start_idx] + new_faq_section + content[faq_end_idx:]
    
    # Update lastmod
    if "lastmod:" in new_content:
        new_content = re.sub(r'^lastmod:.*$', f'lastmod: {current_date}', new_content, flags=re.MULTILINE)
    else:
        if "date:" in new_content:
            new_content = re.sub(r'^(date:.*)$', f'\\1\nlastmod: {current_date}', new_content, flags=re.MULTILINE)
        elif "title:" in new_content:
            new_content = re.sub(r'^(title:.*)$', f'\\1\nlastmod: {current_date}', new_content, flags=re.MULTILINE)

    if content != new_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

files = glob.glob("/home/user/personalized/vesviet/content/**/*.md", recursive=True)
count = 0
for f in files:
    try:
        with open(f, 'r') as fp:
            if "{{< faq" in fp.read():
                continue
        if process_file(f):
            print(f"Updated: {f.replace('/home/user/personalized/vesviet/content/', '')}")
            count += 1
    except Exception as e:
        print(f"Error on {f}: {e}")

print(f"Total updated: {count}")
