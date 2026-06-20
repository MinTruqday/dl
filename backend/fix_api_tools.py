import os
import re

path = 'agentic_ai/src/tools/api_tools.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "/wallets/balance": "/vi-tien/so-du",
    "/wallets/transactions": "/vi-tien/giao-dich",
    "/coupons/redeem": "/ma-giam-gia/su-dung",
    "/withdrawals/revenue": "/rut-tien/doanh-thu",
    "/documents/personal": "/tai-lieu/ca-nhan",
    "/documents/trash": "/tai-lieu/thung-rac",
    "/documents/{document_id}/restore": "/tai-lieu/{document_id}/khoi-phuc",
    "/documents/{document_id}/analyze/dropoff": "/tai-lieu/{document_id}/phan-tich/bo-do",
    "/documents/": "/tai-lieu/",
    "/documents/{document_id}": "/tai-lieu/{document_id}",
    "/deposits": "/nap-tien",
    "/profile/me": "/ho-so/ca-nhan",
    "/inference/translate": "/suy-luan/dich-thuat"
}

for eng, vie in replacements.items():
    content = content.replace(f'"{eng}"', f'"{vie}"')
    content = content.replace(f"'{eng}'", f"'{vie}'")
    content = content.replace(f'INTERNAL_API_URL}}{eng}', f'INTERNAL_API_URL}}{vie}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("api_tools.py fixed")
