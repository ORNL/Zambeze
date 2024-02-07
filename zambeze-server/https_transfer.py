
import os
from flask import Flask, send_file, request, jsonify

app = Flask(__name__)


@app.route('/download')
def download_file():
    try:
        data = request.get_json()

        print(data)

        if 'file_name' in data:
            file_name = data['file_name']

            if os.path.exists(file_name):
                return send_file(file_name, as_attachment=True)
            else:
                return jsonify({'error': 'File not found'}), 404
        else:
            return jsonify({'error': 'File name not provided in request'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500


if __name__ == "__main__":
    app.run(debug=True)
