import re

# 1. Profile Manager (remove streaks and badges methods)
with open('backend/management/src/services/profile.py', 'r') as f:
    content = f.read()

# Remove get_reading_streaks
content = re.sub(r'    @staticmethod\n    async def get_reading_streaks[\s\S]*?(?=    @staticmethod|\Z)', '', content)
# Remove get_badges
content = re.sub(r'    @staticmethod\n    async def get_badges[\s\S]*?(?=    @staticmethod|\Z)', '', content)

with open('backend/management/src/services/profile.py', 'w') as f:
    f.write(content)

# 2. agentic_ai inference router
with open('backend/agentic_ai/src/router/inference.py', 'r') as f:
    content = f.read()

content = re.sub(r'@router\.post\("/sentiment-analysis"\)[\s\S]*?(?=@router|\Z)', '', content)
content = content.replace('    SentimentRequest,\n', '')

with open('backend/agentic_ai/src/router/inference.py', 'w') as f:
    f.write(content)

# 3. schema inference
with open('backend/core/schemas/inference.py', 'r') as f:
    content = f.read()

content = re.sub(r'class SentimentRequest\(BaseModel\):[\s\S]*?(?=class |\Z)', '', content)

with open('backend/core/schemas/inference.py', 'w') as f:
    f.write(content)

# 4. agentic_ai prompt registry
with open('backend/agentic_ai/src/core/prompt_registry.py', 'r') as f:
    content = f.read()

content = re.sub(r'    SENTIMENT_ANALYSIS = "sentiment_analysis"\n', '', content)
content = re.sub(r'    SENTIMENT_SUMMARY = "sentiment_summary"\n', '', content)
content = re.sub(r'        PromptType\.SENTIMENT_ANALYSIS.*?,\n', '', content, flags=re.DOTALL)
content = re.sub(r'        PromptType\.SENTIMENT_SUMMARY.*?,\n', '', content, flags=re.DOTALL)

with open('backend/agentic_ai/src/core/prompt_registry.py', 'w') as f:
    f.write(content)

print("Backend cleanup done.")
