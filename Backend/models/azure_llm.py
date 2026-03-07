import os
from openai import AzureOpenAI

class AzureLLM:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": str(prompt)}
            ],
            temperature=0
        )
        return response.choices[0].message.content

    def generate_content(self, prompt):
        return self.generate(prompt)
