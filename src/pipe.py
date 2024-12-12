from .preprocessor import DataProcessor, TextProcessor, VecProcessor, TimeProcessor
from .encoder import KFDeBERTaTokenizer, KFDeBERTa, ModelTrainer, ModelPredictor
from .database import PostgresDB, DBConnection, TableEditor
from .llm import LLMOpenAI
from datasets import Dataset, DatasetDict
from dotenv import load_dotenv
from tqdm import tqdm
import pandas as pd
import time
import json
import os


class EnvManager:
    def __init__(self, args):
        load_dotenv()
        self.args = args 
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API 키가 로드되지 않았습니다.")
        
        self.model_config, self.db_config = self.__load_configs()
        self.user_tb, self.conf_tb, self.conf_log_tb = 'ibk_poc_user', 'ibk_poc_conf', 'ibk_poc_conf_log'

    def __load_configs(self):
        '''
        llm 모델과 db 설정 파일을 로드합니다.
        '''
        with open(os.path.join(self.args.config_path, 'llm_config.json')) as f:
            llm_config = json.load(f)
 
        with open(os.path.join(self.args.config_path, 'db_config.json')) as f:
            db_config = json.load(f)
        return llm_config, db_config

class PreProcessor:
    def initialize_processor(self):
        return DataProcessor(), TextProcessor(), VecProcessor(), TimeProcessor()
        
class DBManager:
    def __init__(self, db_config):
        self.db_config = db_config

    def initialize_database(self):
        db_connection = DBConnection(self.db_config)
        db_connection.connect()
        postgres = PostgresDB(db_connection)
        table_editor = TableEditor(db_connection)
        return postgres, table_editor

class LLMManager:
    def __init__(self, model_config):
        self.model_config = model_config

    def initialize_openai_llm(self):
        '''
        ChatGPT 인스턴스를 생성하고 반환합니다. 
        '''
        openai_llm = LLMOpenAI(self.model_config)
        openai_llm.set_generation_config()
        return openai_llm
        

class PipelineController:
    def __init__(self, env_manager=None, preprocessor=None, db_manager=None, model_manager=None, llm_manager=None):
        self.env_manager = env_manager 
        self.db_manager = db_manager 
        self.preprocessor = preprocessor 
        self.llm_manager = llm_manager 
    
    def set_env(self):
        self.postgres, self.table_editor = self.db_manager.initialize_database()
        self.data_p, self.text_p, self.vec_p, self.time_p = self.preprocessor.initialize_processor()
        if self.model_manager != None:
            self.openai_llm = self.llm_manager.initialize_openai_llm()

    def process_data(self, input_data):
        '''
        STT 결과 도출한 회의록 파일을, LLM 모델을 사용하여 요약한 후 PostgreSQL conf_log 테이블에 저장합니다.
        
        args:
        input_data (db table): ibk 투자 증권 챗봇을 이용한 사용자들의 대화 로그 [conv_id (pk), date, qa, content, user id]
        
        process:
        Step 1. qa 타입이 'a' (챗봇의 응답) 이거나 이미 데이터베이스에 존재하는 데이터인지 체크한다. 
        Step 2. 그 이외의 경우, 사용자 질문에 대해 encoder 모델, gpt 모델을 활용해 증권 종목 질문 여부를 분류한다. 
          Step 2.1. 성능 개선을 위해, 사용자 질문이 단일 토큰으로 이루어진 경우, tickle list와 매핑해 tickle 관련 질문인지 추가 검사한다.
        Step 3. 사용자가 앱 내 버튼을 클릭한 후 질문을 할 경우, (KR: 333333) 같은 표현값이 대화 기록에 남는다. 이를 활용해 사용자가 
                버튼을 클릭해 들어온 사용자인지 아닌지 분류한다.
        Step 4. 생성한 데이터세트를 PostgreSQL 각 테이블에 저장한다.
        '''
        for idx in tqdm(range(len(input_data))):    
            if input_data[idx][2] == 'A':
                continue
            if self.postgres.check_pk(self.env_manager.cls_tb_name, input_data[idx][0]):    # 데이터베이스에 이미 존재하는 데이터인 경우
                continue

            query = input_data[idx][3]
            self.openai_llm.set_stock_guideline()
            gpt_response = self.openai_llm.get_response(query=query, role=self.openai_llm.system_role, sub_role=self.openai_llm.stock_role)
            encoder_response = self.predictor.predict(query)

            gpt_res = 'o' if gpt_response != '종목 x' else 'x'
            time.sleep(0.2)
            enc_res = 'o' if encoder_response == 'stock' else 'x'
            ensembled_res = gpt_res if gpt_res != enc_res else enc_res

            if len(self.val_tokenizer.tokenize_data(query)) == 1:
                cleaned_word = self.text_p.remove_patterns(query, r"(뉴스|주식|정보|분석)$")    # 불필요한 단어 제거
                ensembled_res = 'o' if cleaned_word in self.tickle_list else 'x'
            '''if ensembled_res == 'o':
                openai_llm.set_stock_tickle_guideline()
                tickle = openai_llm.get_response(input_data[idx][0], role=openai_llm.system_role) 
                stopwords = ['추출', '종목', '죄송']
                if any(stopword in tickle for stopword in stopwords):
                    tickle = '''''
            cls_pred_set = (input_data[idx][0], ensembled_res, gpt_res, enc_res)  
            clicked = 'o' if self.text_p.check_expr(r"\b\w+\(KR:\d+\)", query) else 'x'
            '''if clicked == 'o':
                tickle = re.findall(expr, query)[0]'''
            u_id = input_data[idx][4]
            clicked_set = (input_data[idx][0], clicked, u_id)

            self.table_editor.edit_cls_table('insert', self.env_manager.cls_tb_name, data_type='raw', data=cls_pred_set)
            self.table_editor.edit_clicked_table('insert', self.env_manager.clicked_tb_name, data_type='raw', data=clicked_set)

    def run(self, process='daily', query=None):
        '''
        args:
        '''
        if query:
            self.openai_llm.set_stock_guideline()
            if len(self.val_tokenizer.tokenize_data(query)) == 1:
                cleaned_word = self.text_p.remove_patterns(query, r"(뉴스|주식|정보|분석)$")    # 불필요한 단어 제거
                ensembled_res = 'o' if cleaned_word in self.tickle_list else 'x'
                print(f'해당 쿼리는 종목 분석 {ensembled_res} 질문입니다.')
            response = self.openai_llm.get_response(query=query, role=self.openai_llm.system_role, sub_role=self.openai_llm.stock_role)
            print(f'해당 쿼리는 {response} 질문입니다.')
        else:
            yy, mm, dd = self.time_p.get_previous_day_date()
            crawling_date = yy + mm + dd    # 20240201 형식
            input_data = self.postgres.get_total_data(self.env_manager.conv_tb_name) if process == 'code-test' else \
                self.postgres.get_day_data(self.env_manager.conv_tb_name, crawling_date)
            print(len(input_data))
            self.process_data(input_data)