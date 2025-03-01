import requests
import os

class HoneytokensGenerator:
    def __init__(self, output_dir):
        self.canarytoken_url = "https://your-canarytoken-url.com/api/v1/canarytoken/factory"
        self.canarytoken_api_key = "your-canarytoken-api-key"
        self.output_dir = output_dir

    def generate_pdf_token(self, token_name):
        payload = {
            'factory_auth': self.canarytoken_api_key,
            'memo': token_name,
            'kind': 'doc-msword'
        }
        response = requests.post(self.canarytoken_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            token_url = token_data['canarytoken']
            pdf_response = requests.get(token_url)
            if pdf_response.status_code == 200:
                pdf_path = os.path.join(self.output_dir, f"{token_name}.pdf")
                with open(pdf_path, 'wb') as pdf_file:
                    pdf_file.write(pdf_response.content)
                print(f"Honeytoken PDF generated at: {pdf_path}")
            else:
                print("Failed to download the PDF token.")
        else:
            print("Failed to create the honeytoken.")

if __name__ == "__main__":
    generator = HoneytokensGenerator(output_dir = "/path/to/honeypot/directory")
    generator.generate_pdf_token("example_honeytoken")


    