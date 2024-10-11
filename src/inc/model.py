import os
import logging

logger= logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get('LOGLEVEL', "INFO").upper(), format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from langchain_cohere import ChatCohere
    COHERE_AVAILABLE= True

except ImportError:
    COHERE_AVAILABLE=False

try:
    from langchain_cohere import ChatCohere
    COHERE_AVAILABLE= True

except ImportError:
    COHERE_AVAILABLE=False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_GENAI_AVAILABLE= True

except ImportError:
    GOOGLE_GENAI_AVAILABLE=False


try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE= True

except ImportError:
    GROQ_AVAILABLE=False


class AIModel:
    def __init__(self,model, api_key_var=None, base_url=None) -> None:
        self.model= model or os.getenv('OPENAI_MODEL_NAME', 'gpt-4o')
        if self.model.startswith('openai/'):
            self.api_key_var= "OPENAI_API_KEY"
            self.base_url= "https://api.openai.com/v1"
            self.model_name= self.model.replace('openai/', '')

        elif self.model.startswith('groq/'):
            self.api_key_var= "GROQ_API_KEY"
            self.base_url= "https://api.groq.com/openai/v1"
            self.model_name= self.model.replace('groq/', '')

        elif self.model.startswith('google/'):
            self.api_key_var= 'GOOGLE_API_KEY'
            self.base_url= ''
            self.model_name= self.model.replace('google/', '')

        logger.debug(f'Initialized AIModel with model {self.model_name}, api_key_var {self.api_key_var}')
        self.api_key= os.environ.get(self.api_key_var, 'nokey')


    def get_model(self):
        if self.model.startswith('google/'):
            if GOOGLE_GENAI_AVAILABLE:
                return ChatGoogleGenerativeAI(model= self.model_name, google_api_key= self.api_key)
            else:
                raise ImportError('Google Generative AI model is not yet installed pip install `langchain-google-genai`')
            
        elif self.model.startswith('cohere/'):
            if COHERE_AVAILABLE:
                return ChatCohere(model= self.model_name, google_api_key= self.api_key)
            else:
                raise ImportError('COHERE AI model is not yet installed pip install `langchain-cohere`')