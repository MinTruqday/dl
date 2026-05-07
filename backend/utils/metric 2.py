import re

def calculate_flesch_kincaid(text: str) -> float:
    
    if not text or len(text.strip()) == 0:
        return 0.0
        
    sentences = max(1, len(re.split(r'[.!?]+', text)) - 1)
    words = max(1, len(re.findall(r'\b\w+\b', text)))
    
    syllables = words * 1.5 
    
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return round(max(0, min(100, score)), 2)

def calculate_vocabulary_richness(text: str) -> float:
    
    if not text or len(text.strip()) == 0:
        return 0.0
        
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)
    if total_words == 0:
        return 0.0
        
    unique_words = len(set(words))
    return round((unique_words / total_words) * 100, 2)
