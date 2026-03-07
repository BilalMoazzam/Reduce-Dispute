import os
from models.azure_llm import AzureLLM

class BaseAgent:
    def __init__(self, name, system_prompt, model=None):
        self.name = name
        if isinstance(model, AzureLLM):
            self.llm = model
        else:
            if model is None:
                deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
                if not deployment:
                    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME not set and no model provided")
                model = deployment
            self.llm = AzureLLM(model=model)
        self.system_prompt = system_prompt

    def generate_content(self, query):
        full_prompt = f"{self.system_prompt}\n\nQuery: {query}"
        response = self.llm.generate_content(full_prompt)
        if hasattr(response, 'text'):
            return response
        elif hasattr(response, 'content'):
            class WrappedResponse:
                def __init__(self, text):
                    self.text = text
            return WrappedResponse(str(response.content))
        else:
            class SimpleResponse:
                def __init__(self, text):
                    self.text = text
            return SimpleResponse(str(response))

    async def generate_content_async(self, query):
        full_prompt = f"{self.system_prompt}\n\nQuery: {query}"
        async for chunk in self.llm.generate_content_async(full_prompt):
            yield chunk

    def __call__(self, query):
        return self.generate_content(query)