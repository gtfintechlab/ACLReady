import logging
import os
import tempfile
import time
import zipfile
import tarfile
import sys
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from process_file import process_file

app = Flask(__name__)
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})
status_updates = []

# Configure logging
logging.basicConfig(level=logging.INFO)

def extract_files(file_path, temp_dir):
    """Extracts .tex files from zip or tar.gz archives and returns their paths."""
    tex_files = []

    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            tex_files = [os.path.join(temp_dir, f) for f in zip_ref.namelist() if f.endswith('.tex')]

    elif file_path.endswith('.tar.gz'):
        with tarfile.open(file_path, 'r:gz') as tar_ref:
            tar_ref.extractall(temp_dir)
            tex_files = [os.path.join(temp_dir, f.name) for f in tar_ref.getmembers() if f.isfile() and f.name.endswith('.tex')]

    return tex_files

def merge_tex_files(tex_files, output_file_path):
    """Merges multiple .tex files into one combined .tex file."""
    with open(output_file_path, 'w') as outfile:
        for file_path in tex_files:
            with open(file_path, 'r') as infile:
                content = infile.read()
                outfile.write(content + "\n")  
    logging.info(f"Merged .tex files into {output_file_path}")
    return output_file_path

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), uploaded_file.filename)
    uploaded_file.save(temp_file_path)
    logging.info(f"File saved to {temp_file_path}")

    # Directory to hold extracted files
    temp_dir = tempfile.mkdtemp()
    start_time = time.time()
    processed_data = {}

    try:
        # Determine if we are dealing with a compressed file or a single .tex file
        if uploaded_file.filename.endswith(('.zip', '.tar.gz')):
            # Extract and filter for .tex files only
            tex_files = extract_files(temp_file_path, temp_dir)
            logging.info(f"Extracted .tex files: {tex_files}")

            # Merge extracted .tex files into one combined .tex file
            merged_tex_path = os.path.join(temp_dir, "merged.tex")
            merged_file_path = merge_tex_files(tex_files, merged_tex_path)
            
            # Process the merged .tex file
            processed_data = process_file(merged_file_path)

        elif uploaded_file.filename.endswith('.tex'):
            # Directly process the single .tex file
            processed_data = process_file(temp_file_path)

        else:
            return jsonify({'error': 'Unsupported file format. Only .zip, .tar.gz, and .tex files are allowed.'}), 400

        end_time = time.time()
        time_taken = end_time - start_time
        processed_data['time_taken'] = f"Time taken to generate responses: {time_taken:.6f} seconds"

        return jsonify(processed_data), 200
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/status', methods=['GET'])
def upload_status():
    def event_stream():
        for status in status_updates:
            yield f"data: {status}\n\n"
        status_updates.clear()

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

@app.route('/api/upload/status/update', methods=['POST'])
def status_update():
    status = request.json.get('status')
    if status:
        status_updates.append(status)
    return '', 204

@app.route('/api/helloworld', methods=['GET'])
def hello_world():
    return 'Hello World!'

if __name__ == "__main__":
    app.run(port="8080")
