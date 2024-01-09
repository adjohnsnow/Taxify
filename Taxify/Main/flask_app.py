import os
from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def main(pdf_path):
    # Run your financial data extraction script as a subprocess
    result = subprocess.run(['python', 'main.py', pdf_path], capture_output=True, text=True)
    return result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/extract_data', methods=['POST'])
def extract_data():
    # Assume your form has a file input field named 'file'
    file = request.files['file']

    # Create 'uploads' directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Save the uploaded PDF file
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(pdf_path)

    # Call your financial data extraction script with the PDF file path
    result = main(pdf_path)

    # Remove the uploaded file after processing
    os.remove(pdf_path)

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True)

