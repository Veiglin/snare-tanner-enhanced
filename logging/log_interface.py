from flask import Flask, jsonify, render_template, send_from_directory
import os
import logging

logger = logging.getLogger("log_app_logger")

# Environment and log directory setup
Docker_ENV = os.getenv("Docker_ENV", "false")
log_directory, host = (
    ("/app/logs", "172.29.0.5")
    if Docker_ENV == "True"
    else ("./logs", "0.0.0.0")
)

# Define log file paths
LOG_FILES = {
    "snare_log": os.path.join(log_directory, "snare.log"),
    "snare_err": os.path.join(log_directory, "snare.err"),
    "tanner_log": os.path.join(log_directory, "tanner.log"),
    "tanner_err": os.path.join(log_directory, "tanner.err"),
    "tanner_report": os.path.join(log_directory, "tanner_report.json"),
}

app = Flask(__name__)

@app.route("/")
def landing_page():
    """Landing page."""
    return render_template("landing.html")

@app.route("/logs/snare")
def snare_log():
    """View snare.log."""
    return render_log("snare_log")

@app.route("/logs/snare_err")
def snare_err_log():
    """View snare.err."""
    return render_log("snare_err")

@app.route("/logs/tanner")
def tanner_log():
    """View tanner.log."""
    return render_log("tanner_log")

@app.route("/logs/tanner_err")
def tanner_err_log():
    """View tanner.err."""
    return render_log("tanner_err")

@app.route("/logs/tanner_report")
def tanner_report_log():
    """View tanner_report.json."""
    return render_log("tanner_report")

def render_log(log_name):
    """Helper function to render a log file."""
    log_path = LOG_FILES.get(log_name)
    if not log_path:
        return jsonify({"error": f"Log '{log_name}' not found"}), 404

    if not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' does not exist"}), 404

    try:
        with open(log_path, "r") as f:
            log_content = f.read().replace("\n", "<br>")
        return render_template(f"{log_name}_viewer.html", log_name=log_name, log_content=log_content)
    except Exception as e:
        logger.error(f"Failed to read log '{log_name}': {e}")
        return jsonify({"error": f"Failed to read log '{log_name}': {str(e)}"}), 500

@app.route("/favicon.ico")
def favicon():
    """Serve favicon."""
    return send_from_directory("static", "favicon.ico")

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(host=host, port=5000, debug=(Docker_ENV != "True"))