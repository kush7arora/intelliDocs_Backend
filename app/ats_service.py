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

def calculate_ats_score(text, job_description=None):
    """
    Calculate ATS compatibility score
    
    Args:
        text (str): Resume text
        job_description (str): Optional job description for matching
    
    Returns:
        int: ATS score (0-100)
    """
    score = 0
    max_score = 100
    
    # Contact info (15 points)
    contact = extract_contact_info(text)
    if contact['email']:
        score += 8
    if contact['phone']:
        score += 7
    
    # Sections present (25 points)
    sections = check_resume_sections(text)
    section_score = sum(sections.values()) / len(sections) * 25
    score += section_score
    
    # Skills presence (20 points)
    skills = extract_skills(text)
    total_skills = sum(len(skills_list) for skills_list in skills['technical'].values()) + len(skills['soft'])
    if total_skills > 15:
        score += 20
    elif total_skills > 10:
        score += 15
    elif total_skills > 5:
        score += 10
    else:
        score += 5
    
    # Education (15 points)
    education = extract_education(text)
    if education:
        score += 15
    
    # Experience (15 points)
    experience_years = extract_experience_years(text)
    if experience_years > 5:
        score += 15
    elif experience_years > 2:
        score += 10
    elif experience_years > 0:
        score += 5
    
    # Keyword density (10 points)
    word_count = len(text.split())
    if 400 < word_count < 800:
        score += 10
    elif 300 < word_count < 1000:
        score += 7
    else:
        score += 3
    
    # Job description matching (bonus if provided)
    if job_description:
        match_score = calculate_keyword_match(text, job_description)
        score = int(score * 0.7 + match_score * 0.3)  # Weighted combination
    
    return min(int(score), max_score)

def calculate_keyword_match(resume_text, job_description):
    """
    Calculate keyword match between resume and job description
    
    Args:
        resume_text (str): Resume text
        job_description (str): Job description
    
    Returns:
        int: Match score (0-100)
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    # Extract important words from job description
    jd_words = set(re.findall(r'\b[a-z]{3,}\b', jd_lower))
    resume_words = set(re.findall(r'\b[a-z]{3,}\b', resume_lower))
    
    # Common words to ignore
    stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'from', 'are', 'can'}
    jd_words -= stop_words
    
    # Calculate match
    matched = jd_words.intersection(resume_words)
    match_ratio = len(matched) / len(jd_words) if jd_words else 0
    
    return int(match_ratio * 100)

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
