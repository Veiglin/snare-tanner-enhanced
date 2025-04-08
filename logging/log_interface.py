from flask import Flask, jsonify, send_file
import os

app = Flask(__name__)

# Define the log file paths in the shared volume
LOG_FILES = {
    "snare_log": "/shared_logs/snare.log",
    "snare_err": "/shared_logs/snare.err",
    "tanner_log": "/shared_logs/tanner.log",
    "tanner_err": "/shared_logs/tanner.err",
    "tanner_report": "/shared_logs/tanner_report.json",
}

@app.route('/logs', methods=['GET'])
def list_logs():
    """List all available logs."""
    return jsonify({"available_logs": list(LOG_FILES.keys())})

@app.route('/logs/<log_name>', methods=['GET'])
def get_log(log_name):
    """Fetch a specific log."""
    log_path = LOG_FILES.get(log_name)
    if not log_path:
        return jsonify({"error": f"Log '{log_name}' not found"}), 404

    if not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' does not exist"}), 404

    try:
        return send_file(log_path, as_attachment=False)
    except Exception as e:
        return jsonify({"error": f"Failed to read log '{log_name}': {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

    