"""
File upload routes for the Graph RAG web UI.
Currently handles local file management only; ingestion is triggered elsewhere.
"""

import os
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

upload_bp = Blueprint('upload', __name__)

# Configuration
UPLOAD_FOLDER = os.getenv("RAW_DATA_FOLDER", "./raw_data")
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_uploaded_files():
    """Get list of files in the upload folder."""
    files = []
    upload_path = Path(UPLOAD_FOLDER)
    if upload_path.exists():
        for f in upload_path.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                files.append({
                    'name': f.name,
                    'size': f.stat().st_size,
                    'extension': f.suffix.lower()
                })
    return sorted(files, key=lambda x: x['name'])


@upload_bp.route('/upload')
def upload_page():
    """Render the file upload page."""
    files = get_uploaded_files()
    return render_template('upload.html', files=files)


@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Ensure upload folder exists
    upload_path = Path(UPLOAD_FOLDER)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # Save file
    filename = secure_filename(file.filename)
    filepath = upload_path / filename
    file.save(str(filepath))
    
    return jsonify({
        'success': True,
        'filename': filename,
        'size': filepath.stat().st_size
    })


@upload_bp.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files."""
    files = get_uploaded_files()
    return jsonify({'files': files})


@upload_bp.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific file."""
    filepath = Path(UPLOAD_FOLDER) / secure_filename(filename)
    
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        filepath.unlink()
        return jsonify({'success': True, 'message': f'{filename} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/ingest', methods=['POST'])
def trigger_ingestion():
    """Trigger the ingestion pipeline for uploaded files via RAG API."""
    try:
        import requests
        
        # Call the RAG API's ingestion endpoint
        rag_api_url = os.getenv("RAG_API_URL", "http://rag-api:8000")
        response = requests.post(f"{rag_api_url}/api/v1/ingest", timeout=300)  # 5 min timeout
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'files_processed': data['files_processed'],
                'nodes_created': data['nodes_created'],
                'relationships_created': data['relationships_created'],
                'chunks_embedded': data['chunks_embedded']
            })
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            return jsonify({
                'error': f'Ingestion failed: {error_detail}'
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Ingestion timed out. The process may still be running in the background.'
        }), 504
    except Exception as e:
        return jsonify({
            'error': f'Failed to trigger ingestion: {str(e)}'
        }), 500

