from src import EnvManager, PreProcessor, DBManager, ModelManager, LLMManager, PipelineController
from datetime import timedelta
import argparse 
import schedule
import time
import random
import os 

def main(args):
    env_manager = EnvManager(args)
    preprocessor = PreProcessor()
    db_manager = DBManager(env_manager.db_config)
    pipe = PipelineController(env_manager=env_manager, preprocessor=preprocessor, db_manager=db_manager)   
    pipe.set_env()

    folder_list = os.listdir('./data')
    folder_list = [folder for folder in folder_list if not folder.endswith('.txt')]
    files = [os.listdir(os.path.join('./data', folder)) for folder in folder_list]
    files = [item for sublist in files for item in sublist]
    conf_files = [f for f in files if 'conference' in f]
    summary_files = [f for f in files if 'summary' in f]
    
    user_list = list(range(1, 10+1))
    is_active = False; participant_count = 4
    group_list = ['핑거', 'IBK투자증권', '원라인AI']
    user_name_dict = {1: "익명의 개구리", 2: "익명의 기린", 3: "익명의 거북이", 4: "익명의 고라니", 5: "익명의 강아지", 
                    6: "익명의 고양이", 7: "익명의 두꺼비", 8: "익명의 토끼", 9: "익명의 코알라", 10: "익명의 원숭이"}
    
    for idx in range(1, 10+1):    # user
        try:
            pipe.table_editor.edit_user_tb('insert', pipe.env_manager.user_tb, data_type='raw', data=tuple((idx, is_active, user_name_dict[idx], random.choice(group_list))))
        except:
            pass 

    for idx in range(1, 1 + 18):    # ibk poc conference 
        conf_title = 'test_' + str(idx).zfill(4)
        start_time = pipe.time_p.get_current_time()    # datetime.now()
        end_time = start_time + timedelta(minutes=30) 
        created_by = random.choice(range(1, 10+1))
        folder_no = int(summary_files[idx-1].split('_')[0][-1])
        file_no = int(conf_files[idx-1].split('_')[-1].split('.')[0])
        with open(os.path.join('./data', folder_list[folder_no - 1], summary_files[idx-1]), 'r') as f:
            data = f.readlines()
            txt = ''.join(data)
        
        topic = '토픽_' + str(idx).zfill(2)
        pipe.table_editor.edit_poc_conf_tb('insert', pipe.env_manager.conf_tb, data_type='raw', 
            data=tuple((conf_title, start_time, end_time, created_by, is_active, participant_count, txt, topic)))
        f.close()

    numbers = list(range(1, 19))  # 1부터 10까지의 리스트 생성
    user_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    for idx in range(len(conf_files)):    # confernce log
        folder_no = int(conf_files[idx].split('_')[0][-1])
        file_no = int(conf_files[idx].split('_')[-1].split('.')[0])
        with open(os.path.join('./data', folder_list[folder_no - 1], conf_files[idx]), 'r') as f:
            data = f.readlines()
            for idx2, line in enumerate(data): 
                if line == '\n':
                    continue
                user_no = line.split('|')[0].strip()
                content = line.split('|')[1].strip()
                conf_id = (folder_no - 1) * 3 + file_no
                data = tuple((conf_id, user_dict[user_no], content))
                pipe.table_editor.edit_poc_conf_log_tb('insert', pipe.env_manager.conf_log_tb, data_type='raw', data=data)
               
    '''
    for idx in range(len(summary_files)):    # confernce log
        folder_no = int(summary_files[idx].split('_')[0][-1])
        file_no = int(conf_files[idx].split('_')[-1].split('.')[0])
        with open(os.path.join('./data', folder_list[folder_no - 1], summary_files[idx]), 'r') as f:
            data = f.readlines()
            txt = ''.join(data)
            conf_id = (folder_no - 1) * 3 + file_no 
            pipe.table_editor.edit_poc_conf_summary_tb('insert', pipe.env_manager.conf_summary_tb, data_type='raw', data=tuple((conf_id, txt))) '''
            
    pipe.postgres.db_connection.conn.commit()
    pipe.postgres.db_connection.close()


if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument('--config_path', type=str, default='config/')
    cli_parser.add_argument('--process', type=str, default='daily')
    cli_parser.add_argument('--task_name', type=str, default='cls')
    cli_parser.add_argument('--query', type=str, default=None)
    cli_args = cli_parser.parse_args()
    main(cli_args)