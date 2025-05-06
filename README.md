# Enhancing SNARE/TANNER with Breadcrumbing and Honeytokens utilizing LLM-driven generation

This honeypot framework builds upon the [SNARE](https://github.com/mushorg/snare)/[TANNER](https://github.com/mushorg/tanner/tree/main) honeypot from [T-Pot](https://github.com/telekom-security/tpotce/tree/master) which is designed attract and log interactions on web applications. Within this framework, we extend and enhance SNARE/TANNER by integrating breadcrumbing technics and honeytokens deploy utilizing LLMs for a better and deeper deceptive honeypot framework.

## Key Features

- **Build Upon SNARE/TANNER**: This framework extends SNARE/TANNER honeypot from T-Pot by introducing more advanced deception technique features using breadcrumbing and honeytoken deployment with LLM-driven generation.

- **Breadcrumbs**: This framework have an implemented mechanism to deploy breadcrumbs within a web application utilzing the three different strategies: `robots.txt`, `error pages`, and `html inline comments`.

- **Honeytokens**: This framework includes a mechanism to deploy honeytoken files utilized from [Canarytoken](https://canarytokens.org/nest/generate) including their content, designed to detect unauthorized access. The types of honeytokens supported includes the file types: `docx`, `xlsx`, and `pdf`.

- **Bait Files**: This framework create bait files together with the honeytokens which mimic files that could be exploited. These files are strategically placed to lure the attacker.

- **Utilizing LLMs**: The framework leverages Large Language Models (LLMs) to dynamically generate realistic honeytokens and breadcrumbs content which enhances the deception capabilities of the honeypot.

- **Logging Interface**: The honeypot framework introduces a logging interface for monitoring and analyzing activities in SNARE/TANNER. It captures triggered honeytokens from webhooks which provides insights into the intruders with detailed information about them.

## User Guide

### Configuration in SNARE
The features for the enhanced honeypot is configured using a `config.yml` file created for SNARE which can be founded at the path `/docker/snare/dist`. 

Below is an explanation of the key sections in the configuration file:

- **`FEATURES`**: Parameter to enable or disable the extended framework to generate honeytokens and breadcrumbs.
- **`HONEYTOKEN`**: Specifies the honeytokens associated LLM API and prompt used for generating. At the moment we support [Gemini AI](https://aistudio.google.com/prompts/new_chat) from Google and the [Inference API](https://huggingface.co/docs/inference-providers/index) from Hugging Face. Furthermore, it gives the opportunity to specific a accesible webhook endpoint when triggering a honeytoken.
- **`BREADCRUMB`**: Configures the types of breadcrumbs used and the associated LLM. It furthermore provide options to configure the LLM prompt in each of the used breadcrumb strategies.

Example `config.yml`:
```yaml
FEATURES:
  enabled: True

HONEYTOKEN:
  API-PROVIDER: gemini # Options: huggingface, gemini
  API-ENDPOINT: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash
  API-KEY: foobar123
  PROMPT-FILENAMES: >
    You are generating bait filenames for a website called SmartGadgetStore.live, which sells smart gadgets and electronics online.
    Generate in total 5 files. The generated files should be realistic, code-friendly filenames (no spaces or special characters) that might contain sensitive internal data.
    Examples include inventory backups, customer exports, admin data, supplier lists, or device configuration dumps.
    Use only the file types .docx, .xlsx, .pdf, .db, .sql or .zip and ensure there is minumum one .docx, one .xlsx and one .pdf file.
    Ensure all filenames look authentic and vary slightly each time.
    # Session ID: {session_id}
  PROMPT-FILECONTENT: >
    You are generating bait file content for a website called SmartGadgetStore.live, which sells smart gadgets and electronics online.
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

1. Build and Run the Docker compose file:
     ```bash
     docker compose -f docker/docker-compose-local.yml up --build
     ```

### Setting up a TLS-certificate

### Running with Docker (with TLS-certificate required)

1. Build and Run the Docker compose file:
     ```bash
     docker compose -f docker/docker-compose.yml up --build
     ```

### Logging Interface

The logging interface provides real-time insights into honeypot activity. 




Key features include:

- **Export Options**: Download logs in various formats for further analysis.

#### Navigation

1. Open the logging interface in your browser at `http://localhost:5003`.




