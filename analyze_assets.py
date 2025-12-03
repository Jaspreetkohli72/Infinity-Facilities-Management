import glob
import re
import os

HTML_DIR = r"c:/Users/Jaskaran/Documents/Infinity Facilities Management/Infinity_Facilities_Management"

def analyze_usage():
    html_files = glob.glob(os.path.join(HTML_DIR, '*.html'))
    
    for html_file in html_files:
        print(f"\n--- {os.path.basename(html_file)} ---")
        with open(html_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if 'assets/' in line:
                # Extract the image path
                matches = re.findall(r'assets/[^"\')\s]+', line)
                for match in matches:
                    # Get context (previous and next few lines)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = "".join([l.strip() + " " for l in lines[start:end]])
                    print(f"File: {match}")
                    print(f"Context: {context[:200]}...")

if __name__ == "__main__":
    analyze_usage()
