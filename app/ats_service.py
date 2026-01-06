"""
ATS Service Module
Handles resume analysis, ATS scoring, and keyword matching
"""

import re
import spacy
from collections import Counter
from datetime import datetime

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("Warning: spaCy model not loaded")
    nlp = None

# Common tech skills database
TECH_SKILLS = {
    'languages': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express', 'fastapi', 'rails', 'laravel'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'devops'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'dynamodb', 'cassandra', 'oracle'],
    'tools': ['git', 'jira', 'confluence', 'postman', 'swagger', 'linux', 'agile', 'scrum'],
    'ai_ml': ['machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy']
}

SOFT_SKILLS = [
    'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
    'collaboration', 'project management', 'time management', 'adaptability',
    'critical thinking', 'creativity', 'attention to detail'
]

def detect_document_type(text):
    """
    Automatically detect if document is a resume or meeting transcript
    
    Args:
        text (str): Document text
    
    Returns:
        str: 'resume' or 'transcript'
    """
    text_lower = text.lower()
    
    # Resume indicators
    resume_keywords = [
        'education', 'experience', 'skills', 'objective', 'summary',
        'certifications', 'projects', 'work history', 'professional experience',
        'bachelor', 'master', 'phd', 'degree', 'university', 'college',
        'resume', 'cv', 'curriculum vitae'
    ]
    
    # Transcript indicators
    transcript_keywords = [
        'meeting', 'attendees', 'discussion', 'action items', 'agenda',
        'minutes', 'decisions', 'next steps', 'follow-up', 'adjourned',
        'meeting notes', 'participants', 'date:', 'time:'
    ]
    
    resume_score = sum(1 for keyword in resume_keywords if keyword in text_lower)
    transcript_score = sum(1 for keyword in transcript_keywords if keyword in text_lower)
    
    # Additional checks
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text))
    
    if has_email or has_phone:
        resume_score += 2
    
    if resume_score > transcript_score:
        return 'resume'
    else:
        return 'transcript'

def extract_contact_info(text):
    """
    Extract contact information from resume
    
    Args:
        text (str): Resume text
    
    Returns:
        dict: Contact information
    """
    contact = {
        'email': None,
        'phone': None,
        'linkedin': None,
        'github': None
    }
    
    # Email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        contact['email'] = email_match.group(0)
    
    # Phone
    phone_match = re.search(r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b', text)
    if phone_match:
        contact['phone'] = phone_match.group(0)
    
    # LinkedIn
    linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
    if linkedin_match:
        contact['linkedin'] = linkedin_match.group(0)
    
    # GitHub
    github_match = re.search(r'github\.com/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
    if github_match:
        contact['github'] = github_match.group(0)
    
    return contact

def extract_skills(text):
    """
    Extract technical and soft skills from resume
    
    Args:
        text (str): Resume text
    
    Returns:
        dict: Categorized skills
    """
    text_lower = text.lower()
    
    found_skills = {
        'technical': {},
        'soft': []
    }
    
    # Extract technical skills by category
    for category, skills_list in TECH_SKILLS.items():
        found = [skill for skill in skills_list if skill in text_lower]
        if found:
            found_skills['technical'][category] = found
    
    # Extract soft skills
    found_skills['soft'] = [skill for skill in SOFT_SKILLS if skill in text_lower]
    
    return found_skills

def extract_education(text):
    """
    Extract education information
    
    Args:
        text (str): Resume text
    
    Returns:
        list: Education entries
    """
    education = []
    
    # Degrees
    degree_patterns = [
        r"(Bachelor['\w\s]*|B\.?S\.?|B\.?A\.?|B\.?Tech\.?)",
        r"(Master['\w\s]*|M\.?S\.?|M\.?A\.?|M\.?Tech\.?|MBA)",
        r"(Ph\.?D\.?|Doctorate)"
    ]
    
    for pattern in degree_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            education.append({
                'degree': match.group(0),
                'level': 'undergraduate' if 'bachelor' in match.group(0).lower() or 'b.' in match.group(0).lower() else 'graduate'
            })
    
    return education

def extract_experience_years(text):
    """
    Estimate years of experience from resume
    
    Args:
        text (str): Resume text
    
    Returns:
        int: Estimated years of experience
    """
    # Look for year ranges (e.g., 2020-2023, 2020 - Present)
    year_pattern = r'\b(19|20)(\d{2})\s*[-–—]\s*((19|20)\d{2}|Present|Current)\b'
    matches = re.finditer(year_pattern, text, re.IGNORECASE)
    
    years = []
    try:
        for match in matches:
            start_year_prefix = match.group(1)  # '19' or '20'
            start_year_suffix = match.group(2)  # '00' to '99'
            end_part = match.group(3)           # '2023' or 'Present'
            
            start_year = int(start_year_prefix + start_year_suffix)
            
            if 'present' in end_part.lower() or 'current' in end_part.lower():
                end_year = 2025
            else:
                end_year = int(end_part)
            
            year_diff = end_year - start_year
            if year_diff > 0:  # Only add positive differences
                years.append(year_diff)
    except (ValueError, IndexError):
        pass  # Skip invalid entries
    
    return sum(years) if years else 0

def check_resume_sections(text):
    """
    Check if resume has all essential sections
    
    Args:
        text (str): Resume text
    
    Returns:
        dict: Section presence
    """
    text_lower = text.lower()
    
    sections = {
        'contact_info': bool(re.search(r'@|phone|email|\d{3}[-.]?\d{3}', text)),
        'summary': bool(re.search(r'summary|objective|profile', text_lower)),
        'experience': bool(re.search(r'experience|work history|employment', text_lower)),
        'education': bool(re.search(r'education|degree|university|college', text_lower)),
        'skills': bool(re.search(r'skills|technologies|technical skills', text_lower)),
        'projects': bool(re.search(r'projects|portfolio', text_lower))
    }
    
    return sections


# relies on `nlp` if available in your module (you already set `nlp = spacy.load(...)` or None)
# and on your TECH_SKILLS dict and SOFT_SKILLS list already defined.

# small stopword set for lightweight filtering
_STOPWORDS = {
    'the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'from', 'are', 'can',
    'a', 'an', 'to', 'in', 'on', 'of', 'by', 'is', 'as', 'at', 'or', 'be', 'we', 'our'
}

def _normalize(text: str) -> str:
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text.strip().lower())

def _word_tokens(text: str):
    return re.findall(r'\b[a-z0-9+#.\-]{2,}\b', text.lower())

def _extract_candidate_keywords(text: str):
    """
    Return set of candidate keywords (length >=3), excluding stopwords.
    """
    tokens = _word_tokens(text)
    return set(t for t in tokens if t not in _STOPWORDS and len(t) >= 3)

def discover_unknown_skills(text: str, known_skills_flat: set, min_freq: int = 2):
    """
    Finds repeated candidate tokens that are likely to be skills but not in known_skills_flat.
    Returns a list of discovered skills (lowercase).
    """
    tokens = _word_tokens(text)
    counts = Counter(tokens)
    discovered = [t for t, c in counts.items()
                  if c >= min_freq and t not in known_skills_flat and t not in _STOPWORDS]
    return discovered

def _flatten_known_skills(TECH_SKILLS):
    flat = set()
    for cat, skills in TECH_SKILLS.items():
        for s in skills:
            flat.add(s.lower())
    for s in SOFT_SKILLS:
        flat.add(s.lower())
    return flat

def _semantic_similarity(a: str, b: str, nlp_obj):
    """
    Returns a float between 0.0 and 1.0 representing semantic similarity.
    Falls back to 0 if nlp_obj is None or empty inputs.
    """
    if not nlp_obj or not a or not b:
        return 0.0
    try:
        return max(0.0, min(1.0, nlp_obj(a).similarity(nlp_obj(b))))
    except Exception:
        return 0.0

def _per_term_semantic_matches(resume_terms, jd_terms, nlp_obj, threshold=0.70):
    """
    For each jd_term, see if any resume_term is semantically similar above threshold.
    Returns set of jd_terms that matched semantically.
    """
    if not nlp_obj:
        return set()
    matched = set()
    for j in jd_terms:
        jdoc = nlp_obj(j)
        for r in resume_terms:
            try:
                if jdoc.similarity(nlp_obj(r)) >= threshold:
                    matched.add(j)
                    break
            except Exception:
                continue
    return matched

def calculate_keyword_match(resume_text: str, job_description: str) -> int:
    """
    Backwards-compatible improved keyword match:
    - If spaCy is available, uses document-level semantic similarity (0-1) and returns 0-100.
    - Otherwise falls back to a robust word-overlap ratio (ignore common words).
    """
    if not job_description:
        return 0

    resume_norm = _normalize(resume_text)
    jd_norm = _normalize(job_description)

    # Prefer semantic doc similarity if spaCy is loaded
    global nlp
    if 'nlp' in globals() and nlp:
        try:
            sim = _semantic_similarity(resume_norm, jd_norm, nlp)
            return int(sim * 100)
        except Exception:
            pass

    # fallback: word overlap of important tokens
    jd_tokens = _extract_candidate_keywords(jd_norm)
    resume_tokens = _extract_candidate_keywords(resume_norm)
    jd_tokens = {t for t in jd_tokens if len(t) >= 3}
    resume_tokens = {t for t in resume_tokens if len(t) >= 3}

    if not jd_tokens:
        return 0
    matched = jd_tokens.intersection(resume_tokens)
    match_ratio = len(matched) / len(jd_tokens)
    return int(match_ratio * 100)

def calculate_ats_score(text: str, job_description: str = None) -> int:
    """
    Replacement calculate_ats_score that returns a 0-100 integer.
    Uses a weighted, explainable combination of:
      - contact completeness (10%)
      - section structure quality (15%)
      - skill relevance to JD (30%)
      - experience relevance (20%)
      - semantic keyword match (15%)
      - resume hygiene (10%)
    If no job_description provided, skill relevance is computed as a general 'skill richness' metric.
    """
    text_norm = _normalize(text)
    word_count = len(text_norm.split())

    # ----- contact completeness (0.0 - 1.0) -----
    contact_points = 0.0
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
        contact_points += 0.5
    if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
        contact_points += 0.5
    contact_score = contact_points  # 0..1

    # ----- sections quality (0.0 - 1.0) -----
    sections = check_resume_sections(text)
    # base presence fraction
    presence_frac = sum(bool(v) for v in sections.values()) / len(sections)
    # augment with basic length checks for each present section
    section_length_bonus = 0.0
    for key in ['summary', 'experience', 'education', 'skills', 'projects']:
        if sections.get(key):
            # naive: look for the header and measure following words count
            header_re = re.compile(rf'{key}[:\s]*\n?(.*?)(?:\n\s*\n|$)', re.IGNORECASE | re.DOTALL)
            m = header_re.search(text)
            if m:
                length = len(_normalize(m.group(1)).split())
                section_length_bonus += min(length / 150.0, 1.0) * 0.2  # capped small bonus
    sections_score = min(1.0, presence_frac * 0.8 + section_length_bonus)

    # ----- skills relevance (0.0 - 1.0) -----
    known_flat = _flatten_known_skills(TECH_SKILLS)
    # resume detected skills (from previous extract_skills)
    skills_found = extract_skills(text)
    resume_skill_terms = set()
    for cat, items in skills_found['technical'].items():
        for s in items:
            resume_skill_terms.add(s.lower())
    for s in skills_found['soft']:
        resume_skill_terms.add(s.lower())

    # discover unknown (emerging) skills from resume text
    discovered = discover_unknown_skills(text, known_flat, min_freq=1)
    discovered = [d for d in discovered if d not in resume_skill_terms]
    # add discovered as lower-weight resume terms
    resume_terms_all = set(resume_skill_terms) | set(discovered)

    # derive JD skill terms
    jd_terms = set()
    if job_description:
        jd_tokens = _extract_candidate_keywords(job_description)
        # prefer known skills if present, else jd_tokens
        for k in known_flat:
            if k in job_description.lower():
                jd_terms.add(k)
        jd_terms |= {t for t in jd_tokens if t not in _STOPWORDS}

    global nlp
    skill_relevance = 0.0
    if job_description and jd_terms:
        # exact matches
        exact_matches = resume_terms_all.intersection(jd_terms)
        # semantic matches per-term if spaCy is available
        semantic_matches = set()
        if nlp:
            try:
                semantic_matches = _per_term_semantic_matches(resume_terms_all, jd_terms, nlp, threshold=0.72)
            except Exception:
                semantic_matches = set()
        # discovered matches (lower weight)
        discovered_matches = set(discovered).intersection(jd_terms)

        # compute a weighted fraction:
        exact_count = len(exact_matches)
        semantic_count = len(semantic_matches - exact_matches)
        discovered_count = len(discovered_matches - exact_matches - semantic_matches)

        denom = max(len(jd_terms), 1)
        raw = (exact_count * 1.0 + semantic_count * 0.75 + discovered_count * 0.5) / denom
        skill_relevance = max(0.0, min(1.0, raw))
    else:
        # No JD: compute a 'skill richness' relative score (favoring relevant, not fluff)
        total_tech = sum(len(v) for v in skills_found['technical'].values())
        skill_relevance = min(1.0, total_tech / 12.0)  # 12 solid tech items -> full score

    # ----- experience relevance (0.0 - 1.0) -----
    exp_years = extract_experience_years(text)
    # simple mapping: 0-5 years maps linearly to 0..1, extra years plateau
    experience_relevance = min(1.0, exp_years / 5.0)

    # crude bonus if JD explicitly asks for seniority and resume matches
    if job_description and ('senior' in job_description.lower() or 'lead' in job_description.lower()):
        # require at least 3 years for partial; more for full
        experience_relevance = max(experience_relevance, min(1.0, exp_years / 3.0))

    # ----- semantic keyword match (0.0 - 1.0) -----
    if job_description:
        semantic_km = 0.0
        if 'nlp' in globals() and nlp:
            try:
                semantic_km = _semantic_similarity(text_norm, job_description, nlp)
            except Exception:
                semantic_km = 0.0
        else:
            # fallback to overlap
            jd_tokens = _extract_candidate_keywords(job_description)
            resume_tokens = _extract_candidate_keywords(text)
            if jd_tokens:
                semantic_km = len(jd_tokens.intersection(resume_tokens)) / len(jd_tokens)
        keyword_semantic_score = max(0.0, min(1.0, semantic_km))
    else:
        keyword_semantic_score = 0.0

    # ----- resume hygiene (0.0 - 1.0) -----
    # ideal length: 400-800 words; good: 300-1000
    hygiene = 0.4
    if 400 <= word_count <= 800:
        hygiene = 1.0
    elif 300 <= word_count <= 1000:
        hygiene = 0.8
    elif word_count < 300:
        hygiene = 0.5
    else:
        hygiene = 0.6

    # ----- final weighted aggregation -----
    weights = {
        'contact': 0.10,
        'sections': 0.15,
        'skills': 0.30,
        'experience': 0.20,
        'keywords': 0.15,
        'hygiene': 0.10
    }

    # If JD not provided, reduce keywords weight and move to skills/hygiene
    if not job_description:
        weights['keywords'] = 0.05
        weights['skills'] += 0.10
        weights['hygiene'] += 0.0

    final_score = (
        contact_score * weights['contact'] +
        sections_score * weights['sections'] +
        skill_relevance * weights['skills'] +
        experience_relevance * weights['experience'] +
        keyword_semantic_score * weights['keywords'] +
        hygiene * weights['hygiene']
    )

    # scale to 0-100 and return int
    scaled = int(round(max(0.0, min(1.0, final_score)) * 100))
    return min(100, scaled)


def get_improvement_suggestions_ats(text, sections, skills, contact):
    """
    Generate ATS-specific improvement suggestions
    
    Args:
        text (str): Resume text
        sections (dict): Section presence
        skills (dict): Extracted skills
        contact (dict): Contact info
    
    Returns:
        list: Improvement suggestions
    """
    suggestions = []
    
    # Contact info
    if not contact['email']:
        suggestions.append({
            'priority': 'high',
            'category': 'contact',
            'issue': 'Missing email address',
            'suggestion': 'Add a professional email address at the top of your resume'
        })
    
    if not contact['phone']:
        suggestions.append({
            'priority': 'high',
            'category': 'contact',
            'issue': 'Missing phone number',
            'suggestion': 'Include a phone number for easy contact'
        })
    
    # Sections
    if not sections['summary']:
        suggestions.append({
            'priority': 'medium',
            'category': 'structure',
            'issue': 'No professional summary',
            'suggestion': 'Add a 2-3 sentence professional summary at the top highlighting your key strengths'
        })
    
    if not sections['skills']:
        suggestions.append({
            'priority': 'high',
            'category': 'structure',
            'issue': 'No skills section',
            'suggestion': 'Create a dedicated "Skills" section listing your technical and soft skills'
        })
    
    if not sections['projects']:
        suggestions.append({
            'priority': 'medium',
            'category': 'content',
            'issue': 'No projects section',
            'suggestion': 'Add a "Projects" section showcasing your practical work and achievements'
        })
    
    # Skills count
    total_skills = sum(len(s) for s in skills['technical'].values()) + len(skills['soft'])
    if total_skills < 8:
        suggestions.append({
            'priority': 'medium',
            'category': 'skills',
            'issue': 'Limited skills listed',
            'suggestion': f'You have only {total_skills} skills listed. Add more relevant technical and soft skills (aim for 12-15)'
        })
    
    # Quantification check
    numbers = re.findall(r'\d+%|\$\d+|\d+\+', text)
    if len(numbers) < 3:
        suggestions.append({
            'priority': 'medium',
            'category': 'content',
            'issue': 'Lack of quantifiable achievements',
            'suggestion': 'Add numbers and metrics to your accomplishments (e.g., "Increased efficiency by 30%", "Managed $50K budget")'
        })
    
    return suggestions

def analyze_resume(text, job_description=None):
    """
    Complete ATS resume analysis
    
    Args:
        text (str): Resume text
        job_description (str): Optional job description
    
    Returns:
        dict: Complete ATS analysis
    """
    # Extract all information
    contact = extract_contact_info(text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience_years = extract_experience_years(text)
    sections = check_resume_sections(text)
    ats_score = calculate_ats_score(text, job_description)
    
    # Generate suggestions
    suggestions = get_improvement_suggestions_ats(text, sections, skills, contact)
    
    # Keyword match if job description provided
    keyword_match = None
    if job_description:
        keyword_match = calculate_keyword_match(text, job_description)
    
    return {
        'document_type': 'resume',
        'ats_score': ats_score,
        'contact_info': contact,
        'skills': {
            'technical': skills['technical'],
            'soft': skills['soft'],
            'total_count': sum(len(s) for s in skills['technical'].values()) + len(skills['soft'])
        },
        'education': education,
        'experience_years': experience_years,
        'sections_present': sections,
        'sections_score': f"{sum(sections.values())}/{len(sections)}",
        'keyword_match_score': keyword_match,
        'suggestions': suggestions,
        'suggestion_count': len(suggestions),
        'word_count': len(text.split()),
        'analyzed_at': datetime.utcnow().isoformat()
    }
