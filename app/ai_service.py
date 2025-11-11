"""
AI Service Module
Handles text summarization, improvement suggestions, and key information extraction
"""

try:
    from transformers import pipeline
except Exception as e:
    print("⚠️ Transformers not available:", e)
    pipeline = None
import spacy
import re
from datetime import datetime

# Load spaCy model for text processing
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Warning: spaCy model not loaded. Run: python -m spacy download en_core_web_sm")
    nlp = None

# Initialize summarization pipeline (lazy loading)
_summarizer = None

def get_summarizer():
    """
    Lazy load the summarization model to avoid startup delays.
    Falls back to a dummy summarizer if transformers/torch are unavailable.
    """
    global _summarizer

    if _summarizer is not None:
        return _summarizer

    if pipeline is None:
        # Fallback dummy summarizer (no ML)
        print("⚠️ Using dummy summarizer (no transformers installed).")
        _summarizer = lambda text, **kwargs: [
            {"summary_text": text[:300] + "... (summary unavailable)"}
        ]
        return _summarizer

    try:
        print("Loading summarization model... (may take a minute first time)")
        _summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # CPU
        )
        print("✅ Summarization model loaded successfully!")
    except Exception as e:
        print("⚠️ Could not load summarizer:", e)
        _summarizer = lambda text, **kwargs: [
            {"summary_text": text[:300] + "... (summary unavailable)"}
        ]
    return _summarizer

def summarize_text(text, max_length=150, min_length=50):
    """
    Generate a concise summary of the input text
    
    Args:
        text (str): Input text to summarize
        max_length (int): Maximum length of summary in tokens
        min_length (int): Minimum length of summary in tokens
    
    Returns:
        dict: Summary and metadata
    """
    try:
        # Handle short texts
        if len(text.split()) < 30:
            return {
                'summary': text,
                'note': 'Text is too short to summarize effectively',
                'original_length': len(text.split()),
                'summary_length': len(text.split())
            }
        
        # Get summarizer
        summarizer = get_summarizer()
        
        # BART has a max input length of 1024 tokens
        # Truncate if necessary
        words = text.split()
        if len(words) > 900:  # Leave buffer for tokenization
            text = ' '.join(words[:900])
        
        # Generate summary
        result = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        
        summary = result[0]['summary_text']
        
        return {
            'summary': summary,
            'original_length': len(text.split()),
            'summary_length': len(summary.split()),
            'compression_ratio': round(len(summary.split()) / len(text.split()), 2)
        }
    
    except Exception as e:
        return {
            'summary': None,
            'error': str(e),
            'note': 'Summarization failed'
        }

def extract_action_items(text):
    """
    Extract action items from text using pattern matching and NLP
    
    Args:
        text (str): Input text
    
    Returns:
        list: Extracted action items
    """
    action_items = []
    
    # Common action item patterns
    patterns = [
        r'(?i)action items?:?\s*(.*?)(?:\n\n|\Z)',
        r'(?i)to[- ]do:?\s*(.*?)(?:\n\n|\Z)',
        r'(?i)tasks?:?\s*(.*?)(?:\n\n|\Z)',
        r'(?i)next steps?:?\s*(.*?)(?:\n\n|\Z)',
    ]
    
    # Extract using patterns
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            items_text = match.group(1)
            # Split by newlines or bullet points
            items = re.split(r'\n[-•*]|\n\d+\.', items_text)
            for item in items:
                item = item.strip()
                if item and len(item) > 10:  # Filter out very short items
                    action_items.append(item)
    
    # Also look for verb-based action patterns
    verb_patterns = [
        r'(?i)(?:need to|must|should|will|going to|have to)\s+([^.!?\n]{10,100})',
        r'(?i)(?:complete|finish|prepare|review|update|send|schedule)\s+([^.!?\n]{10,100})',
    ]
    
    for pattern in verb_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            item = match.group(0).strip()
            if item and item not in action_items:
                action_items.append(item)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_items = []
    for item in action_items:
        item_lower = item.lower()
        if item_lower not in seen:
            seen.add(item_lower)
            unique_items.append(item)
    
    return unique_items[:10]  # Return top 10 action items

def extract_key_decisions(text):
    """
    Extract key decisions from meeting notes
    
    Args:
        text (str): Input text
    
    Returns:
        list: Key decisions
    """
    decisions = []
    
    # Decision patterns
    patterns = [
        r'(?i)(?:decided|agreed|approved|concluded)\s+(?:to|that|on)\s+([^.!?\n]{10,150})',
        r'(?i)(?:decision|resolution|agreement):?\s*([^.!?\n]{10,150})',
        r'(?i)(?:we will|we shall|it was decided)\s+([^.!?\n]{10,150})',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            decision = match.group(0).strip()
            if decision and decision not in decisions:
                decisions.append(decision)
    
    return decisions[:5]  # Return top 5 decisions

def suggest_improvements(text):
    """
    Suggest improvements for documentation clarity
    
    Args:
        text (str): Input text
    
    Returns:
        dict: Improvement suggestions
    """
    suggestions = []
    
    # Check for structure
    has_headings = bool(re.search(r'^[A-Z][^.!?\n]{3,50}:?\s*$', text, re.MULTILINE))
    if not has_headings:
        suggestions.append({
            'type': 'structure',
            'issue': 'No clear headings or sections',
            'suggestion': 'Add clear section headings like "Discussion Points", "Decisions", "Action Items"'
        })
    
    # Check for dates
    has_date = bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4}', text))
    if not has_date:
        suggestions.append({
            'type': 'metadata',
            'issue': 'No date found',
            'suggestion': 'Add the meeting/document date at the top'
        })
    
    # Check for attendees
    has_attendees = bool(re.search(r'(?i)(?:attendees?|participants?|present):', text))
    if not has_attendees and 'meeting' in text.lower():
        suggestions.append({
            'type': 'metadata',
            'issue': 'No attendees listed',
            'suggestion': 'List meeting attendees for better context'
        })
    
    # Check for action items
    has_actions = bool(re.search(r'(?i)(?:action items?|to[- ]do|tasks?|next steps?):', text))
    if not has_actions:
        suggestions.append({
            'type': 'content',
            'issue': 'No clear action items section',
            'suggestion': 'Add an "Action Items" section to track follow-ups'
        })
    
    # Check text length
    word_count = len(text.split())
    if word_count < 50:
        suggestions.append({
            'type': 'completeness',
            'issue': 'Document is very short',
            'suggestion': 'Consider adding more detail about discussions and outcomes'
        })
    elif word_count > 1000:
        suggestions.append({
            'type': 'conciseness',
            'issue': 'Document is very long',
            'suggestion': 'Consider breaking into sections or creating a summary at the top'
        })
    
    # Check for unclear language
    passive_voice_count = len(re.findall(r'\b(?:was|were|been|being)\s+\w+ed\b', text))
    if passive_voice_count > 5:
        suggestions.append({
            'type': 'clarity',
            'issue': 'Frequent use of passive voice',
            'suggestion': 'Use active voice for clearer communication (e.g., "John completed" instead of "was completed by John")'
        })
    
    return {
        'total_suggestions': len(suggestions),
        'suggestions': suggestions,
        'word_count': word_count,
        'readability_score': calculate_simple_readability(text)
    }

def calculate_simple_readability(text):
    """
    Calculate a simple readability score (0-100, higher is more readable)
    Based on sentence length and word complexity
    
    Args:
        text (str): Input text
    
    Returns:
        int: Readability score
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 50
    
    # Average words per sentence
    words = text.split()
    avg_sentence_length = len(words) / len(sentences) if sentences else 0
    
    # Penalize very long sentences
    length_score = max(0, 100 - (avg_sentence_length - 15) * 2)
    
    # Check for complex words (>7 characters)
    complex_words = [w for w in words if len(w) > 7]
    complexity_ratio = len(complex_words) / len(words) if words else 0
    complexity_score = max(0, 100 - complexity_ratio * 100)
    
    # Combined score
    readability = int((length_score + complexity_score) / 2)
    
    return max(0, min(100, readability))

def analyze_text(text):
    """
    Comprehensive text analysis combining all AI features
    
    Args:
        text (str): Input text
    
    Returns:
        dict: Complete analysis results
    """
    return {
        'summary': summarize_text(text),
        'action_items': extract_action_items(text),
        'key_decisions': extract_key_decisions(text),
        'improvements': suggest_improvements(text),
        'analyzed_at': datetime.utcnow().isoformat()
    }
