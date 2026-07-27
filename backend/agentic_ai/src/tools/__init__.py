from src.tools.editing import (
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits,
)
from src.tools.billing import (
    get_user_balance,
    get_transaction_history,
    redeem_voucher,
    get_revenue_report,
    transfer_user_funds,
)
from src.tools.document import (
    get_my_documents,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics,
    read_document,
    recommend_documents,
)
from src.tools.mindmap import generate_mindmap
from src.tools.instructions import manage_user_instructions
from src.workflow.reduction import agent_summarize_long_document

tools = [
    agent_summarize_long_document,
    get_user_balance,
    get_transaction_history,
    transfer_user_funds,
    redeem_voucher,
    get_revenue_report,
    get_my_documents,
    read_document,
    recommend_documents,
    generate_mindmap,
    manage_user_instructions,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics,
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits,
]


