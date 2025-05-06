# Enhancing SNARE/TANNER with Breadcrumbing and Honeytokens utilizing LLM-driven generation

This honeypot framework builds upon the [SNARE](https://github.com/mushorg/snare)/[TANNER](https://github.com/mushorg/tanner/tree/main) honeypot from [T-Pot](https://github.com/telekom-security/tpotce/tree/master) which is designed attract and log interactions on web applications. Within this framework, we extend and enhance SNARE/TANNER by integrating breadcrumbing technics and honeytokens deploy utilizing LLMs for a better and deeper deceptive honeypot framework.

## Overall Features

- **Build Upon SNARE/TANNER**: This framework extends SNARE/TANNER honeypot from T-Pot by introducing more advanced deception technique features using breadcrumbing and honeytoken deployment with LLM-driven generation.
- **Breadcrumbs**: This framework have an implemented mechanism to deploy breadcrumbs within a web application utilzing the three different strategies: `robots.txt`, `error pages`, and `html inline comments`.
- **Honeytokens**: This framework includes a mechanism to deploy honeytoken files utilized from [Canarytoken](https://canarytokens.org/nest/generate) including their content, designed to detect unauthorized access. The types of honeytokens supported includes the file types: `docx`, `xlsx`, and `pdf`.
- **Bait Files**: This framework create bait files together with the honeytokens which mimic files that could be exploited. These files are strategically placed to lure the attacker.
- **Utilizing LLMs**: The framework leverages Large Language Models (LLMs) to dynamically generate realistic honeytokens and breadcrumbs content which enhances the deception capabilities of the honeypot.
- **Logging Interface**: The honeypot framework introduces a logging interface for monitoring and analyzing activities in SNARE/TANNER. It captures triggered honeytokens from webhooks which provides insights into the intruders with detailed information about them.

## User Guide

Here describe how to set up and run the honeypot framework.

### Configuration in SNARE
The features for the enhanced honeypot is configured using a `config.yml` file created for SNARE which can be founded at the path `/docker/snare/dist`. 

Below is an explanation of the key sections in the configuration file:

- **`FEATURES`**: Parameter to enable or disable the extended framework to generate honeytokens and breadcrumbs.
- **`DOMAIN`**: Variable specifying the absolute domain used for running the framework with TLS.
- **`HONEYTOKEN`**: Specifies the honeytokens associated LLM API and prompt used for generating. At the moment we support [Gemini AI](https://aistudio.google.com/prompts/new_chat) from Google and the [Inference API](https://huggingface.co/docs/inference-providers/index) from Hugging Face. Furthermore, it gives the opportunity to specific a accesible webhook endpoint when triggering a honeytoken.
- **`BREADCRUMB`**: Configures the types of breadcrumbs used and the associated LLM. It furthermore provide options to configure the LLM prompt in each of the used breadcrumb strategies.

For both of them:

- **API-PROVIDER**:
- **API-ENDPOINT**:
- **API-KEY**:
- **LLM-PARAMETERS**:

Specific for `HONEYTOKENS`:

- **PROMPT-FILENAMES**:
- **PROMPT-FILECONTENT**:
- **WEBHOOK-URL**:

Within the `BREADCRUMB`:

- **TYPES**:
- **PROMPT-ERROR-PAGE**:
- **PROMPT-HTML-COMMENT**:

Here is an example `config.yml`:
```yaml
FEATURES:
  enabled: True

DOMAIN:
  ABS_DOMAIN: electronicstore.live

HONEYTOKEN:
  API-PROVIDER: gemini # Options: huggingface, gemini
  API-ENDPOINT: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash
  API-KEY: foobar123
  PROMPT-FILENAMES: >
    You are generating bait filenames for a website called electronicstore.live, which sells smart gadgets and electronics online.
    Generate in total 5 files. The generated files should be realistic, code-friendly filenames (no spaces or special characters) that might contain sensitive internal data.
    Examples include inventory backups, customer exports, admin data, supplier lists, or device configuration dumps.
    Use only the file types .docx, .xlsx, .pdf, .db, .sql or .zip and ensure there is minumum one .docx, one .xlsx and one .pdf file.
    Ensure all filenames look authentic and vary slightly each time.
    # Session ID: {session_id}
  PROMPT-FILECONTENT: >
    You are generating bait file content for a website called electronicstore.live, which sells smart gadgets and electronics online.
    For each of the filenames {honeytoken} generated, create realistic and believable content that might be found in a file.
    Examples of this could be inventory backups, customer exports, admin data, supplier lists, or device configuration dumps.
  LLM-PARAMETERS:
    temperature: 1.3
    top_p: 0.95
    top_k: 50
    max_new_tokens: 400
    do_sample: true # Only for HuggingFace
    return_full_text: false # Only for HuggingFace
  WEBHOOK-URL:   

BREADCRUMB:
  TYPES: # Options: robots, error_page, html_comments
  - robots
  - error_page
  - html_comments
  API-PROVIDER: gemini # Options: huggingface, gemini
  API-ENDPOINT: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash
  API-KEY: foobar123
  PROMPT-ERROR-PAGE: >
    Write a short HTML bait line (in a <p> tag) that subtly hints at an internal file located at /{honeytoken}. 
    It should look like something a developer accidentally left in, referencing the file path naturally.
    Your goal is to lead a potential attacker to believe that this is a legitimate file path. 
  PROMPT-HTML-COMMENT: >
    Write a realistic one-line HTML comment like a developer's note.
    It should mention /{honeytoken} as if it's a config file or temporary log.
    Do NOT include HTML tags or '--'. Make it look like leftover debug info."
  LLM-PARAMETERS:
    temperature: 0.9
    top_p: 0.95
    top_k: 50
    max_new_tokens: 50
    do_sample: true # Only for HuggingFace
    return_full_text: false # Only for HuggingFace
```

### Running Locally with Docker (without TLS-certificate required)

1. Build and Run the local Docker compose file `docker-compose-local.yml`:
     ```bash
     docker compose -f docker/docker-compose-local.yml up --build
     ```

### Setting up a TLS-certificate (domain required)

Before running the web application honeypot with TLS, you need to obtain and install a valid certificate for your domain (e.g., electronicstore.live). This needs to be setted up from [Let’s Encrypt using Certbot](https://certbot.eff.org/):

1. Install Certbot on your system that is going to host the web application honeypot:

    ```bash
    sudo apt-get update && sudo apt-get install certbot
    ```
    
2. Request a certificate for your domain:
    ```bash
    sudo certbot certonly --standalone -d electronicstore.live
    ```

3. The following certificates will be stored under `/etc/letsencrypt/live/{domain_name}/` on the host system:

- `fullchain.pem`
- `privkey.pem`


### Running with Docker (with TLS-certificate required)

1. Build and Run the Docker compose file `docker-compose.yml`:
     ```bash
     docker compose -f docker/docker-compose.yml up --build
     ```

Within the application code, TLS is enabled when IS_LOCAL is not set to true. Here is a code snippet of that take part of it in the file `/snare/snare/server.py`:

```python
is_local = os.getenv("IS_LOCAL", "false").lower() == "true"

if not is_local:
    abs_domain = SnareConfig.get("DOMAIN", "ABS_DOMAIN")
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
      certfile=f'/etc/letsencrypt/live/{abs_domain}/fullchain.pem',
      keyfile=f'/etc/letsencrypt/live/{abs_domain}/privkey.pem'
    )
    site = web.TCPSite(
        self.runner,
        self.run_args.host_ip,
        self.run_args.port,
        ssl_context=ssl_context
    )
else:
    site = web.TCPSite(
        self.runner,
        self.run_args.host_ip,
        self.run_args.port
    )
```

## Logging Interface

Building and running the honeypot using docker will also build and run a logging interface built in Python using [`gunicorn`](https://gunicorn.org/) - providing a WSGI HTTP server from Unix - with HTML-templates.
The logging interface provides real-time insights into honeypot activity of the SNARE and TANNER services respectively through a user-friendly dashboard that is easy to navigate.

The key functionalities include:
- **Browse Logs & Errors**: The logging interface enables the user to view and navigate through system logs and error logs for both SNARE & TANNER. Every log and error log entry is saved until the data is removed.
- **Browse Received Webhooks**: The logging interface enables the user to view received webhooks for the triggered honeytokens - which is data sent from canarytoken. All webhooks is keept infinitely until data is removed. 
- **Export Logs, Errors & Webhook Data**: The interface gives the options to download all logs and error logs in their respective formats for further analysis.
- **Clear Logs & Webhooks**: The interface allows the user to reset the captured logs by clearing either individual logs or all logs and webhooks.
- **Real-Time Updates**: The interface dynamically updates the logs and webhook data when new data is received which provides real-time insights into honeypot activity without having to refresh the page.

### Navigating the Interface

To open the logging interface, open your browser at `http://localhost:5003` or `http://0.0.0.0:5003` from where the index-page will get showed. Each log and error log types (e.g., snare.log, tanner.err) together with the webhooks is accessible via dedicated sections showed on the index-page, and users can seamlessly switch between them using the navigation menu. In the danger-zone, the user can delete all logs and by then reset the whole logging interface.

When opening one of the sections, logs are displayed in reserve chronological order for easier access to the newest and most recent entries. The specific log can be downloaded clicking the blue button in the below corner to the right. In the same corner, the user is able to clean the log, error log or saved webhooks when browsing the specific section by clicking the red buttom in the below right corner.


