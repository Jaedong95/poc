from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
from transformers import GenerationConfig
from openai import OpenAI
import torch

# 특정 경고 메시지 무시
# warnings.filterwarnings("ignore", category=UserWarning, message="TypedStorage is deprecated")

class LLMModel():
    def __init__(self, config):
        self.config = config 

    def set_gpu(self, model):
        self.device = torch.device("cuda") if torch.cuda.is_available() else "cpu"    
        model.to(self.device)
    
    def set_generation_config(self, max_tokens=500, temperature=0.9):
        self.gen_config = {
            "max_tokens": max_tokens,
            "temperature": temperature
        }

class LLMOpenAI(LLMModel):
    def __init__(self, config, openai_api_key):
        super().__init__(config)
        self.client = OpenAI(api_key=openai_api_key)

    def set_generation_config(self):
        self.gen_config = {
            "max_tokens": self.config['max_tokens'],
            "temperature": self.config['temperature']
        }

    def set_grammer_guideline(self):
        self.system_role = """
        너는 생성된 문장에서, 맞춤법 및 어법을 교정해주는 전문가야. 어색한 문장을 자연스럽게 바꿔주는 역할만 해주면 돼. 
        """
        self.sub_role = """
        어색한 문장 교정 예시는 다음과 같아.
        렉을 그치기 위한 작업  -> RAG를 구축하기 위한 작업
        """
        
    def get_response(self, query, role="너는 금융권에서 일하고 있는 조수로, 사용자 질문에 대해 간단 명료하게 답을 해주면 돼", sub_role="", model='gpt-4o'):
        try:
            sub_role = sub_role
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": role},
                    {"role": "system", "content": sub_role},
                    {"role": "user", "content": query},
                ],
                max_tokens=self.gen_config['max_tokens'],
                temperature=self.gen_config['temperature'],
            )
        except Exception as e:
            return f"Error: {str(e)}"
        return response.choices[0].message.content
