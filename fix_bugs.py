# 1. fix compilation schema CompileRequest
filepath = 'backend/compilation/src/schemas/composition.py'
with open(filepath, 'r') as f:
    content = f.read()
content = content.replace('content: Any', 'content: str')
with open(filepath, 'w') as f:
    f.write(content)

# 2. fix content api bookmark.py
filepath = 'backend/content/src/api/bookmark.py'
with open(filepath, 'r') as f:
    content = f.read()
content = content.replace('data.bookmark_ids', 'data.document_ids')
with open(filepath, 'w') as f:
    f.write(content)

# 3. fix payment api wallet.py
filepath = 'backend/payment/src/api/wallet.py'
with open(filepath, 'r') as f:
    content = f.read()
content = content.replace('payload.coupon_code', 'payload.code')
with open(filepath, 'w') as f:
    f.write(content)
