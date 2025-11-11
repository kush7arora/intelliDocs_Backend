from app.ats_service import detect_document_type, analyze_resume
from app.ai_service import summarize_text, extract_action_items, extract_key_decisions, suggest_improvements, analyze_text
from app.pdf_generator import create_resume_pdf, create_transcript_pdf
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import uuid
import os
import tempfile
from datetime import datetime
from app.utils import allowed_file, extract_text_from_file, get_file_size_mb
from app.format_converter import convert_format
from werkzeug.utils import secure_filename
import mimetypes
# Create Blueprint for API routes
api = Blueprint('api', __name__)

# Temporary in-memory storage (data will be lost on restart/deployment)
transcripts_db = {}

@api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API is running
    """
    return jsonify({
        'status': 'healthy',
        'message': 'IntelliDocs API is running',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@api.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Upload transcript file (.txt, .pdf, .doc, .docx)
    
    Form data:
        - file: The file to upload
        - title: (optional) Title for the transcript
        - user_id: (optional) User identifier
    
    Returns:
        JSON response with transcript_id and metadata
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed',
                'allowed_types': list(current_app.config['ALLOWED_EXTENSIONS'])
            }), 400
        
        # Secure the filename
        original_filename = secure_filename(file.filename)
        
        # Generate unique ID for this transcript
        transcript_id = str(uuid.uuid4())
        
        # Get additional form data
        title = request.form.get('title', original_filename)
        user_id = request.form.get('user_id', 'demo_user')
        
        # Create unique filename
        unique_filename = f"{transcript_id}_{original_filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file to uploads folder
        file.save(file_path)
        
        # Extract text from file
        text_content = extract_text_from_file(file_path)
        
        # Get file metadata
        file_size_mb = get_file_size_mb(file_path)
        
        # Store transcript metadata
        transcript_data = {
            'id': transcript_id,
            'user_id': user_id,
            'title': title,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size_mb': file_size_mb,
            'text': text_content,
            'text_length': len(text_content),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'uploaded',
            'summary': None,
            'improvements': None,
            'action_items': None,
            'key_decisions': None
        }
        
        transcripts_db[transcript_id] = transcript_data
        
        return jsonify({
            'message': 'File uploaded successfully',
            'transcript_id': transcript_id,
            'data': {
                'id': transcript_id,
                'title': title,
                'filename': original_filename,
                'file_size_mb': file_size_mb,
                'text_length': len(text_content),
                'created_at': transcript_data['created_at']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_mimetype(file_format):
    """Get MIME type for format"""
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    return mime_types.get(file_format.lower(), 'application/octet-stream')

@api.route('/convert_format', methods=['POST'])
def convert_format_endpoint():
    """
    Convert file format (PDF ↔ DOCX ↔ TXT)
    
    Form data:
        - file: File to convert
        - target_format: Target format (pdf, docx, txt)
    
    Returns:
        Converted file download
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        target_format = request.form.get('target_format', '').lower()
        if target_format not in ['pdf', 'docx', 'txt']:
            return jsonify({'error': 'Invalid target format. Use: pdf, docx, or txt'}), 400
        
        # Determine source format from file extension
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        if file_ext not in ['pdf', 'docx', 'txt', 'doc']:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Normalize file extension
        if file_ext == 'doc':
            file_ext = 'docx'
        
        # Same format check
        if file_ext == target_format:
            return jsonify({'error': 'Source and target formats are the same'}), 400
        
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_input = os.path.join(temp_dir, f"temp_{uuid.uuid4()}.{file_ext}")
        file.save(temp_input)
        
        # Convert format
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_converted_{timestamp}.{target_format}"
        temp_output = os.path.join(temp_dir, output_filename)
        
        try:
            convert_format(temp_input, temp_output, file_ext, target_format, base_name)
            
            # Send file
            return send_file(
                temp_output,
                mimetype=get_mimetype(target_format),
                as_attachment=True,
                download_name=output_filename
            )
        finally:
            # Cleanup temp input
            if os.path.exists(temp_input):
                os.remove(temp_input)
    
    except Exception as e:
        print(f"Conversion error: {str(e)}")  # ✅ Add this for debugging
        import traceback
        traceback.print_exc()  # ✅ Print full error
        return jsonify({'error': str(e)}), 500





@api.route('/export_pdf/<transcript_id>', methods=['GET'])
def export_pdf(transcript_id):
    """
    Export analysis results as PDF
    
    URL parameter:
        - transcript_id: ID of the document
    
    Returns:
        PDF file download
    """
    try:
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Document not found'}), 404
        
        document = transcripts_db[transcript_id]
        doc_type = document.get('document_type', 'transcript')
        
        # Create temporary file for PDF
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{doc_type}_analysis_{timestamp}.pdf"
        output_path = os.path.join(temp_dir, filename)
        
        # Generate appropriate PDF based on document type
        if doc_type == 'resume':
            analysis_data = {
                'analysis': document.get('ats_analysis', {})
            }
            create_resume_pdf(analysis_data, output_path)
        else:
            analysis_data = {
                'analysis': {
                    'summary': {
                        'summary': document.get('summary'),
                        'original_length': len(document.get('text', '').split()),
                        'summary_length': len(document.get('summary', '').split()) if document.get('summary') else 0,
                        'compression_ratio': round(len(document.get('text', '').split()) / max(len(document.get('summary', '').split()), 1), 2) if document.get('summary') else 0
                    },
                    'action_items': document.get('action_items', []),
                    'key_decisions': document.get('key_decisions', []),
                    'improvements': document.get('improvements', {})
                }
            }
            create_transcript_pdf(analysis_data, output_path)
        
        # Send file
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500






@api.route('/upload_text', methods=['POST'])
def upload_text():
    """
    Upload transcript as raw text (alternative to file upload)
    
    JSON body:
        - text: The transcript text
        - title: (optional) Title for the transcript
        - user_id: (optional) User identifier
    
    Returns:
        JSON response with transcript_id and metadata
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text field is required'}), 400
        
        text = data['text']
        title = data.get('title', 'Untitled Transcript')
        user_id = data.get('user_id', 'demo_user')
        
        # Generate unique ID
        transcript_id = str(uuid.uuid4())
        
        # Store transcript
        transcript_data = {
            'id': transcript_id,
            'user_id': user_id,
            'title': title,
            'text': text,
            'text_length': len(text),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'uploaded',
            'summary': None,
            'improvements': None,
            'action_items': None,
            'key_decisions': None
        }
        
        transcripts_db[transcript_id] = transcript_data
        
        return jsonify({
            'message': 'Text uploaded successfully',
            'transcript_id': transcript_id,
            'data': {
                'id': transcript_id,
                'title': title,
                'text_length': len(text),
                'created_at': transcript_data['created_at']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/summarize', methods=['POST'])
def summarize():
    """
    Generate AI summary for a transcript
    
    JSON body:
        - transcript_id: ID of the transcript to summarize
        - max_length: (optional) Maximum summary length
    
    Returns:
        JSON response with summary and extracted information
    """
    try:
        data = request.get_json()
        transcript_id = data.get('transcript_id')
        
        if not transcript_id:
            return jsonify({'error': 'transcript_id is required'}), 400
        
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Transcript not found'}), 404
        
        transcript = transcripts_db[transcript_id]
        text = transcript['text']
        
        # Get optional parameters
        max_length = data.get('max_length', 150)
        
        # Generate summary
        summary_result = summarize_text(text, max_length=max_length)
        
        # Extract action items and decisions
        action_items = extract_action_items(text)
        key_decisions = extract_key_decisions(text)
        
        # Update transcript with results
        transcript['summary'] = summary_result.get('summary')
        transcript['action_items'] = action_items
        transcript['key_decisions'] = key_decisions
        transcript['status'] = 'analyzed'
        transcript['analyzed_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            'message': 'Summarization completed successfully',
            'transcript_id': transcript_id,
            'results': {
                'summary': summary_result,
                'action_items': action_items,
                'key_decisions': key_decisions,
                'action_items_count': len(action_items),
                'key_decisions_count': len(key_decisions)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/improve', methods=['POST'])
def improve():
    """
    Get AI-powered documentation improvement suggestions
    
    JSON body:
        - transcript_id: ID of the transcript to analyze
    
    Returns:
        JSON response with improvement suggestions
    """
    try:
        data = request.get_json()
        transcript_id = data.get('transcript_id')
        
        if not transcript_id:
            return jsonify({'error': 'transcript_id is required'}), 400
        
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Transcript not found'}), 404
        
        transcript = transcripts_db[transcript_id]
        text = transcript['text']
        
        # Generate improvement suggestions
        improvements = suggest_improvements(text)
        
        # Update transcript
        transcript['improvements'] = improvements
        
        return jsonify({
            'message': 'Analysis completed successfully',
            'transcript_id': transcript_id,
            'improvements': improvements
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/analyze', methods=['POST'])
def analyze():
    """
    Complete AI analysis: summarize + extract + suggest improvements
    
    JSON body:
        - transcript_id: ID of the transcript to analyze
    
    Returns:
        JSON response with complete analysis
    """
    try:
        data = request.get_json()
        transcript_id = data.get('transcript_id')
        
        if not transcript_id:
            return jsonify({'error': 'transcript_id is required'}), 400
        
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Transcript not found'}), 404
        
        transcript = transcripts_db[transcript_id]
        text = transcript['text']
        
        # Run complete analysis
        analysis = analyze_text(text)
        
        # Update transcript with all results
        transcript['summary'] = analysis['summary'].get('summary')
        transcript['action_items'] = analysis['action_items']
        transcript['key_decisions'] = analysis['key_decisions']
        transcript['improvements'] = analysis['improvements']
        transcript['status'] = 'analyzed'
        transcript['analyzed_at'] = analysis['analyzed_at']
        
        return jsonify({
            'message': 'Complete analysis finished',
            'transcript_id': transcript_id,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@api.route('/smart_analyze', methods=['POST'])
def smart_analyze():
    """
    Smart analysis that auto-detects if document is resume or transcript
    and routes to appropriate analyzer
    
    JSON body:
        - transcript_id: ID of the document to analyze
        - job_description: (optional) For resume matching
        - force_type: (optional) 'resume' or 'transcript' to override detection
    
    Returns:
        JSON response with appropriate analysis
    """
    try:
        data = request.get_json()
        transcript_id = data.get('transcript_id')
        job_description = data.get('job_description')
        force_type = data.get('force_type')
        
        if not transcript_id:
            return jsonify({'error': 'transcript_id is required'}), 400
        
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Document not found'}), 404
        
        document = transcripts_db[transcript_id]
        text = document['text']
        
        # Detect document type (or use forced type)
        if force_type:
            doc_type = force_type
        else:
            doc_type = detect_document_type(text)
        
        # Route to appropriate analyzer
        if doc_type == 'resume':
            analysis = analyze_resume(text, job_description)
            
            # Update document with results
            document['document_type'] = 'resume'
            document['ats_score'] = analysis['ats_score']
            document['ats_analysis'] = analysis
            document['status'] = 'analyzed'
            document['analyzed_at'] = analysis['analyzed_at']
            
            return jsonify({
                'message': 'Resume analysis completed',
                'document_id': transcript_id,
                'document_type': 'resume',
                'analysis': analysis
            }), 200
        
        else:  # transcript
            # Use existing transcript analysis
            from app.ai_service import analyze_text
            analysis = analyze_text(text)
            
            # Update document with results
            document['document_type'] = 'transcript'
            document['summary'] = analysis['summary'].get('summary')
            document['action_items'] = analysis['action_items']
            document['key_decisions'] = analysis['key_decisions']
            document['improvements'] = analysis['improvements']
            document['status'] = 'analyzed'
            document['analyzed_at'] = analysis['analyzed_at']
            
            return jsonify({
                'message': 'Transcript analysis completed',
                'document_id': transcript_id,
                'document_type': 'transcript',
                'analysis': analysis
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/analyze_resume', methods=['POST'])
def analyze_resume_endpoint():
    """
    Dedicated resume analysis endpoint
    
    JSON body:
        - transcript_id: ID of the resume document
        - job_description: (optional) Job description for keyword matching
    
    Returns:
        JSON response with ATS analysis
    """
    try:
        data = request.get_json()
        transcript_id = data.get('transcript_id')
        job_description = data.get('job_description')
        
        if not transcript_id:
            return jsonify({'error': 'transcript_id is required'}), 400
        
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Document not found'}), 404
        
        document = transcripts_db[transcript_id]
        text = document['text']
        
        # Analyze resume
        analysis = analyze_resume(text, job_description)
        
        # Update document
        document['document_type'] = 'resume'
        document['ats_score'] = analysis['ats_score']
        document['ats_analysis'] = analysis
        document['status'] = 'analyzed'
        document['analyzed_at'] = analysis['analyzed_at']
        
        return jsonify({
            'message': 'Resume ATS analysis completed',
            'document_id': transcript_id,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/result/<transcript_id>', methods=['GET'])
def get_result(transcript_id):
    """
    Fetch transcript and all associated results
    
    URL parameter:
        - transcript_id: ID of the transcript
    
    Returns:
        JSON response with complete transcript data
    """
    try:
        if transcript_id not in transcripts_db:
            return jsonify({'error': 'Transcript not found'}), 404
        
        transcript = transcripts_db[transcript_id]
        
        # Don't send file_path in response (security)
        response_data = {k: v for k, v in transcript.items() if k != 'file_path'}
        
        return jsonify({
            'data': response_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/search', methods=['POST'])
def search():
    """
    Search across all transcripts
    
    JSON body:
        - query: Search query string
        - user_id: (optional) Filter by user
    
    Returns:
        JSON response with matching transcripts
    """
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        user_id = data.get('user_id')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Filter transcripts
        results = []
        for transcript in transcripts_db.values():
            # Filter by user_id if provided
            if user_id and transcript['user_id'] != user_id:
                continue
            
            # Search in title and text
            if query in transcript['title'].lower() or query in transcript['text'].lower():
                # Don't include full text in search results
                result_item = {
                    'id': transcript['id'],
                    'title': transcript['title'],
                    'text_preview': transcript['text'][:200] + '...' if len(transcript['text']) > 200 else transcript['text'],
                    'created_at': transcript['created_at'],
                    'status': transcript['status']
                }
                results.append(result_item)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/transcripts', methods=['GET'])
def list_transcripts():
    """
    List all transcripts for a user
    
    Query parameters:
        - user_id: (optional) Filter by user (default: all users)
    
    Returns:
        JSON response with list of transcripts
    """
    try:
        user_id = request.args.get('user_id')
        
        # Filter transcripts
        results = []
        for transcript in transcripts_db.values():
            if user_id and transcript['user_id'] != user_id:
                continue
            
            # Summary info only
            result_item = {
                'id': transcript['id'],
                'title': transcript['title'],
                'text_length': transcript['text_length'],
                'created_at': transcript['created_at'],
                'status': transcript['status'],
                'has_summary': transcript.get('summary') is not None
            }
            results.append(result_item)
        
        # Sort by created_at (newest first)
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'transcripts': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
