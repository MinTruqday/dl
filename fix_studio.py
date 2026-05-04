import re

path = 'frontend/app/(main)/studio/page.tsx'
with open(path, 'r') as f:
    text = f.read()

# Fix imports
text = re.sub(
    r'import \{([^}]+compileDocumentAPI[^}]+)\} from "@/app/lib/api";',
    r'import { compileDocumentAPI, getDocumentDraftAPI, getDocumentsAPI, publishDocumentAPI, saveDocumentDraftAPI, updateDocumentAPI } from "@/services/document.service";\nimport { requestPayoutDetailedAPI } from "@/services/monetization.service";\nimport { API_URL } from "@/services/auth.service";\nimport { getWalletBalanceAPI as getWalletAPI, getDetailedHistoryAPI as getTransactionsAPI } from "@/services/wallet.service";',
    text
)

# Remove old imports that are now broken
text = re.sub(
    r'import \{([^}]+getWalletAPI[^}]+)\} from "@/app/lib/api";',
    r'',
    text
)
# Ensure TiptapEditor import path is correct if exists
text = text.replace('@/app/components/editor/', '@/components/editor/')
text = text.replace('@/app/components/', '@/components/')

with open(path, 'w') as f:
    f.write(text)
