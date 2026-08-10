from src.tools.editing import (
    read_document_section,
    edit_document_text,
    edit_document_block,
    propose_document_edits,
)
from src.tools.billing import get_user_balance, get_transaction_history, get_revenue_report
from src.tools.document import (
    search_editorjs_capabilities,
    create_document,
    update_document_metadata,
    replace_document_content,
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
from src.tools.mcp import execute_mcp_tool, search_mcp_connectors, suggest_mcp_connectors
from src.workflow.reduction import agent_summarize_long_document
from src.tools.code import execute_python

tools = [
    agent_summarize_long_document,
    execute_python,
    search_editorjs_capabilities,
    create_document,
    update_document_metadata,
    replace_document_content,
    get_user_balance,
    get_transaction_history,
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
    search_mcp_connectors,
    suggest_mcp_connectors,
    execute_mcp_tool,
]
