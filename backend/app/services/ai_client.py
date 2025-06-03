"""
AI model client configuration and management
"""
import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

def create_model_client():
    """Create and return the Azure OpenAI model client."""
    return AzureOpenAIChatCompletionClient(
        model=os.environ["AZURE_OPENAI_MODEL_NAME"],
        azure_deployment=os.environ["AZURE_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )