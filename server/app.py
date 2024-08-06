import logging
import os
import json
import tempfile
import time
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from process_file import process_file

app = Flask(__name__)

cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

status_updates = []

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_file_path)
    logging.info(f"File saved to {temp_file_path}")

    start_time = time.time()  # Record the start time

    # Call the external Python script
    try:
        # Process the file
        data = process_file(temp_file_path)

        end_time = time.time()  # Record the end time
        time_taken = end_time - start_time
        data['time_taken'] = f"Time taken to generate responses: {time_taken:.6f} seconds"
        
        return jsonify(data), 200
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