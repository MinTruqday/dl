import os
import re

forbidden_words = ["hệ thống", "dịch vụ", "an toàn", "cơ chế", "toàn cầu", "chức năng"]
forbidden_pattern = re.compile(r'\b(' + '|'.join(forbidden_words) + r')\b', re.IGNORECASE)

findings = []

for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                if re.search(r'["\'].*[\u0080-\uFFFF]+.*["\']', line): # Contains non-ascii (vietnamese) in a string
                    # check for forbidden words
                    # extract string literals first
                    strings = re.findall(r'["\']([^"\']*)["\']', line)
                    for s in strings:
                        if forbidden_pattern.search(s):
                            findings.append((path, i+1, s))

with open('forbidden_findings.txt', 'w', encoding='utf-8') as out:
    for path, line, s in findings:
        out.write(f"{path}:{line} -> {s}\n")
print(f"Found {len(findings)} occurrences.")
