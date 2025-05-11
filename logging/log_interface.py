from flask import Flask, jsonify, render_template, send_from_directory, request
import os
from markupsafe import Markup  # Update this import
import logging
import json
from webhook_storage import load_webhooks, save_webhook, clear_webhooks, download_webhook

def print_color(msg, mode="INFO", end="\n"):
    colors = {
        "INFO": "\033[97m",  # white
        "ERROR": "\033[31m",  # red
        "WARNING": "\033[33m",  # yellow
    }
    try:
        color = colors[mode]
    except KeyError:
        color = colors["INFO"]
    print(color + str(msg) + "\033[0m", end=end)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("log_app_logger")
logger.setLevel(logging.INFO)

# Environment and log directory setup
Docker_ENV = os.getenv("Docker_ENV", "false")
log_directory = "/shared_logs"

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

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint to receive POST requests."""
    try:
        # Ensure the request has a JSON body
        if not request.is_json:
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 400

        data = request.get_json()  # Safely parse JSON payload
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        # Save the webhook data to persistent storage
        save_webhook(data)

        return jsonify({"message": "Webhook received successfully"}), 200
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route("/webhooks", methods=["GET"])
def view_webhooks():
    """View all received webhooks."""
    try:
        raw_webhooks = load_webhooks()  # Load webhooks from persistent storage
        # Convert each dict → single-line JSON string, with literal < and >
        single_line = [
            Markup(
                json.dumps(
                    wh,
                    ensure_ascii=False,
                    separators=(',', ': ')
                )
            )
            for wh in raw_webhooks
        ]
        return render_template("webhooks.html", webhooks=single_line)
    except Exception as e:
        logger.error(f"Error rendering webhooks: {e}")
        return jsonify({"error": "Failed to load webhooks"}), 500

def render_log(log_name):
    """Helper function to render a log file."""
    log_path = LOG_FILES.get(log_name)
    if not log_path:
        return jsonify({"error": f"Log '{log_name}' not found"}), 404

    if not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' does not exist"}), 404

    try:
        if log_name == "tanner_report":
            with open(log_path, "r") as f:
                raw = [line.strip() for line in f if line.strip()]

            parsed = []
            for line in raw:
                try:
                    obj = json.loads(line)
                    parsed.append(json.dumps(obj, separators=(",", ":")))
                except json.JSONDecodeError:
                    parsed.append(line)
                    
            page_size   = 50
            first_page  = parsed[:page_size]
            next_offset = page_size if page_size < len(parsed) else None

            return render_template(
                f"{log_name}_viewer.html",
                log_name=log_name,
                log_content=first_page,
                next_offset=next_offset
            )
        else:
            with open(log_path, "r") as f:
                lines = [line.rstrip() for _, line in zip(range(500), f)]
                log_content = "<br>".join(lines)

        return render_template(f"{log_name}_viewer.html",
                            log_name=log_name,
                            log_content=log_content)

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

@app.route("/download/<log_name>", methods=["GET"])
def download_log(log_name):
    """Download a log file."""
    log_path = LOG_FILES.get(log_name)
    if not log_path or not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' not found"}), 404

    try:
        return send_from_directory(
            directory=os.path.dirname(log_path),
            path=os.path.basename(log_path),
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Failed to download log '{log_name}': {e}")
        return jsonify({"error": f"Failed to download log '{log_name}': {str(e)}"}), 500
    
@app.route("/clear/<log_name>", methods=["POST"])
def clear_log(log_name):
    """Clear the content of a log file."""
    log_path = LOG_FILES.get(log_name)
    if not log_path or not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' not found"}), 404

    try:
        # Clear the content of the log file
        open(log_path, "w").close()
        logger.info(f"Cleared log file: {log_name}")
        return jsonify({"message": f"Log file '{log_name}' cleared successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to clear log '{log_name}': {e}")
        return jsonify({"error": f"Failed to clear log '{log_name}': {str(e)}"}), 500
    
@app.route("/clear_webhooks", methods=["POST"])
def clear_webhooks_route():
    """Clear all webhooks."""
    try:
        # Clear the webhooks from persistent storage
        clear_webhooks()
        logger.info("Cleared all webhooks")
        return jsonify({"message": "All webhooks cleared successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to clear webhooks: {e}")
        return jsonify({"error": f"Failed to clear webhooks: {str(e)}"}), 500

@app.route("/download_webhooks", methods=["GET"])
def download_webhook_route():
    """Download the webhook storage file."""
    try:
        file_path = download_webhook()
        if not file_path:
            return jsonify({"error": "Webhook storage file does not exist"}), 404

        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Failed to download webhook storage file: {e}")
        return jsonify({"error": f"Failed to download webhook storage file: {str(e)}"}), 500
    
@app.route("/logs/<log_name>/batch/<int:offset>")
def load_log_batch(log_name, offset):
    log_path = LOG_FILES.get(log_name)
    if not log_path or not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_name}' not found"}), 404

    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            batch_size = 50 if log_name == "tanner_report" else 500
            batch = lines[offset:offset + batch_size]
            return jsonify({
                "lines": [line.rstrip() for line in batch],
                "next_offset": offset + batch_size if offset + batch_size < len(lines) else None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/webhooks/batch/<int:offset>")
def load_webhook_batch(offset):
    try:
        with open("webhooks.json", "r") as f:
            webhooks = json.load(f)
        batch = webhooks[offset:offset + 100]
        return jsonify({
            "webhooks": batch,
            "next_offset": offset + 100 if offset + 100 < len(webhooks) else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/wipe_all", methods=["POST"])
def wipe_all():
    """Wipe all logs and webhooks."""
    try:
        # Clear all log files
        for log_name, log_path in LOG_FILES.items():
            if os.path.exists(log_path):
                open(log_path, "w").close()
                logger.info(f"Cleared log file: {log_name}")

        # Clear all webhooks
        clear_webhooks()
        logger.info("Cleared all webhooks")

        return jsonify({"message": "All logs and webhooks wiped successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to wipe all data: {e}")
        return jsonify({"error": f"Failed to wipe all data: {str(e)}"}), 500

