import re

registry_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/core/prompt_registry.py"
inference_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/api/inference.py"

# Add Enums
with open(registry_path, "r") as f:
    reg_content = f.read()

new_enums = """
    TRANSLATE = "translate"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SENTIMENT_SUMMARY = "sentiment_summary"
    IMAGE_COVER = "image_cover"
    CODE_GENERATION = "code_generation"
    GRAMMAR_CHECK = "grammar_check"
    FLASHCARD_GENERATOR = "flashcard_generator"
    SUMMARIZE = "summarize"
    AUTOCOMPLETE = "autocomplete"
    AI_SUGGESTIONS = "ai_suggestions"
    CHECK_LOGIC = "check_logic"
    SYNONYMS = "synonyms"
    MINDMAP = "mindmap"
    SUGGEST_CITATIONS = "suggest_citations"
    TRANSFORM_TONE = "transform_tone"
    MULTI_DOC_SYNTHESIS = "multi_doc_synthesis"
"""

if "TRANSLATE = " not in reg_content:
    reg_content = reg_content.replace('    DOCUMENT_GENERATION = "document_generation"', 
                                      '    DOCUMENT_GENERATION = "document_generation"' + new_enums)

new_prompts = """
        PromptType.TRANSLATE: "SYSTEM IDENTITY: DocLib Core System - Translation Engine.\\nOBJECTIVE: Translate the following text into {target_lang}. Output ONLY the translated text.\\n\\nTEXT:\\n{text}",
        PromptType.SENTIMENT_ANALYSIS: "SYSTEM IDENTITY: DocLib Core System - Sentiment Engine.\\nOBJECTIVE: Analyze the sentiment of the following text. Output ONLY one word: Positive, Negative, or Neutral.\\n\\nTEXT:\\n{text}",
        PromptType.SENTIMENT_SUMMARY: "SYSTEM IDENTITY: DocLib Core System - Sentiment Engine.\\nOBJECTIVE: Based on the following reviews, write a one-sentence summary of the overall reader sentiment.\\nOUTPUT_LANGUAGE: Must match the language of the reviews.\\n\\nREVIEWS: {reviews}",
        PromptType.IMAGE_COVER: "Book cover for {title}. Description: {description}. Style: {style}. High quality, cinematic.",
        PromptType.CODE_GENERATION: "SYSTEM IDENTITY: DocLib Core System - Code Generation Engine.\\nOBJECTIVE: Write clean and efficient {language} code for the following request. Output ONLY the code block.\\n\\nREQUEST:\\n{prompt}",
        PromptType.GRAMMAR_CHECK: "SYSTEM IDENTITY: DocLib Core System - Grammar Engine.\\nOBJECTIVE: Check and correct all spelling and grammar errors in the following text. Output ONLY the corrected text.\\nOUTPUT_LANGUAGE: Must match the language of the input text.\\n\\nTEXT:\\n{text}",
        PromptType.FLASHCARD_GENERATOR: "SYSTEM IDENTITY: DocLib Core System - Learning Engine.\\nOBJECTIVE: Create a high-quality flashcard with a front (question) and back (answer) based on the given text and context. Output ONLY valid JSON: {{'front': 'question', 'back': 'answer'}}.\\nOUTPUT_LANGUAGE: Must match the language of the input text.\\n\\nCONTEXT: {context}\\nTEXT: {text}",
        PromptType.SUMMARIZE: "SYSTEM IDENTITY: DocLib Core System - Summary Engine.\\nOBJECTIVE: Provide a concise summary of the following content in {language}.\\n\\nTEXT:\\n{text}",
        PromptType.AUTOCOMPLETE: "SYSTEM IDENTITY: DocLib Core System - Autocomplete Engine.\\nOBJECTIVE: Write one natural continuation sentence for the following text without repeating existing content. OUTPUT_LANGUAGE: Must match the input text language.\\nCONTEXT: {context}\\nTEXT: {text}",
        PromptType.AI_SUGGESTIONS: "SYSTEM IDENTITY: DocLib Core System - Ideation Engine.\\nOBJECTIVE: Based on the context, suggest 3 development directions for this content. OUTPUT_LANGUAGE: Must match the input text language.\\nCONTEXT: {context}\\nTEXT: {text}",
        PromptType.CHECK_LOGIC: "SYSTEM IDENTITY: DocLib Core System - Logic Engine.\\nOBJECTIVE: Check for logical contradictions, plot holes, or character inconsistencies. OUTPUT_LANGUAGE: Must match the input text language.\\nCONTEXT: {context}\\nTEXT: {text}",
        PromptType.SYNONYMS: "SYSTEM IDENTITY: DocLib Core System - Thesaurus Engine.\\nOBJECTIVE: Find synonyms for the following word or phrase. Output ONLY a comma-separated list.\\nOUTPUT_LANGUAGE: Must match the language of the input.\\n\\nINPUT: {text}",
        PromptType.MINDMAP: 'SYSTEM IDENTITY: DocLib Core System - Mindmap Engine.\\nOBJECTIVE: Analyze the following text and generate a mindmap structure with depth {depth}. Output ONLY a single valid JSON object with no markdown or extra text. JSON structure: {{"nodes": [{{"id": "root", "label": "node"}}], "edges": [{{"from": "root", "to": "node"}}]}}.\\nOUTPUT_LANGUAGE: Labels must match the language of the input text.\\n\\nTEXT: {text}',
        PromptType.SUGGEST_CITATIONS: "SYSTEM IDENTITY: DocLib Core System - Citation Engine.\\nOBJECTIVE: Based on the user's text and the reference sources found, suggest citations in {style} format.\\nOUTPUT_LANGUAGE: Must match the language of the user's text.\\n\\nUSER TEXT: {text}\\n\\nREFERENCE SOURCES:\\n{sources}",
        PromptType.TRANSFORM_TONE: "SYSTEM IDENTITY: DocLib Core System - Tone Engine.\\nOBJECTIVE: {action} the following text to match the tone '{tone}'. Preserve core meaning while adjusting the linguistic style.\\nOUTPUT_LANGUAGE: Must match the language of the input text.\\n\\nTEXT: {text}",
        PromptType.MULTI_DOC_SYNTHESIS: "SYSTEM IDENTITY: DocLib Core System - Synthesis Engine.\\nOBJECTIVE: Synthesize information from multiple documents to answer the query: '{query}'.\\nOUTPUT_LANGUAGE: Must match the language of the query.\\n\\nCONTEXT:\\n{context}"
    }
"""

if "PromptType.TRANSLATE:" not in reg_content:
    reg_content = reg_content.replace('    }', new_prompts)

with open(registry_path, "w") as f:
    f.write(reg_content)


# Update inference.py
with open(inference_path, "r") as f:
    inf_content = f.read()

replacements = [
    (r'prompt = f"OBJECTIVE: Translate the following text into \{req\.target_lang\}\. Output ONLY the translated text\.\\n\\nTEXT:\\n\{req\.text\}"', 
     'prompt = prompt_registry.get(PromptType.TRANSLATE).format(target_lang=req.target_lang, text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Analyze the sentiment of the following text\. Output ONLY one word: Positive, Negative, or Neutral\.\\n\\nTEXT:\\n\{text\}"',
     'prompt = prompt_registry.get(PromptType.SENTIMENT_ANALYSIS).format(text=text)'),
     
    (r'summary_prompt = f"OBJECTIVE: Based on the following reviews, write a one-sentence summary of the overall reader sentiment\.\\nOUTPUT_LANGUAGE: Must match the language of the reviews\.\\n\\nREVIEWS: \{\'; \'\.join\(texts_to_analyze\[:5\]\)\}"',
     'summary_prompt = prompt_registry.get(PromptType.SENTIMENT_SUMMARY).format(reviews="; ".join(texts_to_analyze[:5]))'),
     
    (r'prompt = f"Book cover for \{req\.title\}\. Description: \{req\.description\}\. Style: \{req\.style\}\. High quality, cinematic\."',
     'prompt = prompt_registry.get(PromptType.IMAGE_COVER).format(title=req.title, description=req.description, style=req.style)'),
     
    (r'prompt = f"OBJECTIVE: Write clean and efficient \{req\.language\} code for the following request\. Output ONLY the code block\.\\n\\nREQUEST:\\n\{req\.prompt\}"',
     'prompt = prompt_registry.get(PromptType.CODE_GENERATION).format(language=req.language, prompt=req.prompt)'),
     
    (r'prompt = f"OBJECTIVE: Check and correct all spelling and grammar errors in the following text\. Output ONLY the corrected text\.\\nOUTPUT_LANGUAGE: Must match the language of the input text\.\\n\\nTEXT:\\n\{req\.text\}"',
     'prompt = prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Create a high-quality flashcard with a front \(question\) and back \(answer\) based on the given text and context\. Output ONLY valid JSON: \{\{\'front\': \'question\', \'back\': \'answer\'\}\}\.\\nOUTPUT_LANGUAGE: Must match the language of the input text\.\\n\\nCONTEXT: \{req\.context\}\\nTEXT: \{req\.text\}"',
     'prompt = prompt_registry.get(PromptType.FLASHCARD_GENERATOR).format(context=req.context, text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Provide a concise summary of the following content in \{req\.language\}\.\\n\\nTEXT:\\n\{req\.text\}"',
     'prompt = prompt_registry.get(PromptType.SUMMARIZE).format(language=req.language, text=req.text)'),
     
    (r'"autocomplete": f"OBJECTIVE: Write one natural continuation sentence for the following text without repeating existing content\. OUTPUT_LANGUAGE: Must match the input text language\.\\nCONTEXT: \{req\.context\}\\nTEXT: \{req\.text\}"',
     '"autocomplete": prompt_registry.get(PromptType.AUTOCOMPLETE).format(context=req.context, text=req.text)'),
     
    (r'"grammar": f"OBJECTIVE: Fix all grammar and spelling errors\. Output ONLY the corrected text\. OUTPUT_LANGUAGE: Must match the input text language\.\\nTEXT: \{req\.text\}"',
     '"grammar": prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)'),
     
    (r'"summarize": f"OBJECTIVE: Provide a concise summary\. OUTPUT_LANGUAGE: Must match the input text language\.\\nTEXT: \{req\.text\}"',
     '"summarize": prompt_registry.get(PromptType.SUMMARIZE).format(language="the input language", text=req.text)'),
     
    (r'"ai_suggestions": f"OBJECTIVE: Based on the context, suggest 3 development directions for this content\. OUTPUT_LANGUAGE: Must match the input text language\.\\nCONTEXT: \{req\.context\}\\nTEXT: \{req\.text\}"',
     '"ai_suggestions": prompt_registry.get(PromptType.AI_SUGGESTIONS).format(context=req.context, text=req.text)'),
     
    (r'"check_logic": f"OBJECTIVE: Check for logical contradictions, plot holes, or character inconsistencies\. OUTPUT_LANGUAGE: Must match the input text language\.\\nCONTEXT: \{req\.context\}\\nTEXT: \{req\.text\}"',
     '"check_logic": prompt_registry.get(PromptType.CHECK_LOGIC).format(context=req.context, text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Find synonyms for the following word or phrase\. Output ONLY a comma-separated list\.\\nOUTPUT_LANGUAGE: Must match the language of the input\.\\n\\nINPUT: \{req\.text\}"',
     'prompt = prompt_registry.get(PromptType.SYNONYMS).format(text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Analyze the following text and generate a mindmap structure with depth \{req\.depth\}\. Output ONLY a single valid JSON object with no markdown or extra text\. JSON structure: \{\{\\"nodes\\": \[\{\{\\"id\\": \\"root\\", \\"label\\": \\"node\\"\}\}\], \\"edges\\": \[\{\{\\"from\\": \\"root\\", \\"to\\": \\"node\\"\}\}\]\}\}\.\\nOUTPUT_LANGUAGE: Labels must match the language of the input text\.\\n\\nTEXT: \{req\.text\[:2000\]\}"',
     'prompt = prompt_registry.get(PromptType.MINDMAP).format(depth=req.depth, text=req.text[:2000])'),
     
    (r'prompt = f"OBJECTIVE: Based on the user\'s text and the reference sources found, suggest citations in \{req\.style\} format\.\\nOUTPUT_LANGUAGE: Must match the language of the user\'s text\.\\n\\nUSER TEXT: \{req\.text\}\\n\\nREFERENCE SOURCES:\\n" \+ "\\n"\.join\(sources\)',
     'prompt = prompt_registry.get(PromptType.SUGGEST_CITATIONS).format(style=req.style, text=req.text, sources="\\n".join(sources))'),
     
    (r'prompt = f"OBJECTIVE: \{action\.capitalize\(\)\} the following text to match the tone \'\{req\.tone\}\'\. Preserve core meaning while adjusting the linguistic style\.\\nOUTPUT_LANGUAGE: Must match the language of the input text\.\\n\\nTEXT: \{req\.text\}"',
     'prompt = prompt_registry.get(PromptType.TRANSFORM_TONE).format(action=action.capitalize(), tone=req.tone, text=req.text)'),
     
    (r'prompt = f"OBJECTIVE: Synthesize information from multiple documents to answer the query: \'\{req\.query\}\'\.\\nOUTPUT_LANGUAGE: Must match the language of the query\.\\n\\nCONTEXT:\\n" \+ "\\n"\.join\(all_context\[:10\]\)',
     'prompt = prompt_registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(query=req.query, context="\\n".join(all_context[:10]))')
]

for old, new in replacements:
    inf_content = re.sub(old, new, inf_content)

with open(inference_path, "w") as f:
    f.write(inf_content)

print("Inference prompts replaced.")
