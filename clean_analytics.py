import re

path = 'frontend/app/(main)/analytics/page.tsx'
with open(path, 'r') as f:
    content = f.read()

# 1. Remove import
content = re.sub(r'import \{ analyzeSentimentAPI as getDocumentSentimentAPI \} from "@/features/ai/services/inference\.service";\n', '', content)

# 2. Remove states
content = re.sub(r'  const \[sentiment, setSentiment\] = useState<any>\(null\);\n', '', content)
content = re.sub(r'  const \[selectedDocumentId, setSelectedDocumentId\] = useState\(""\);\n', '', content)

# 3. Remove analyzeSentiment function
content = re.sub(r'  const analyzeSentiment = async \(\) => \{[\s\S]*?\};\n\n', '', content)

# 4. Remove the entire bottom grid that contains the sentiment UI
# The div starts at: <div className="grid lg:grid-cols-12 gap-16 animate-in fade-in slide-in-from-bottom-8 duration-300"
# and ends before the last 2 closing divs of the component.
# I can use multi_replace if I know exactly where, but regex works if carefully bounded.
# Let's just find the index of `<div className="grid lg:grid-cols-12` and the `</div>\n    </div>\n  );\n}` at the end.
start_idx = content.find('      <div\n        className="grid lg:grid-cols-12')
end_idx = content.rfind('    </div>\n  );\n}')
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

with open(path, 'w') as f:
    f.write(content)
print("Analytics page cleaned.")
