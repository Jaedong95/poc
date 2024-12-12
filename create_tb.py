from src import EnvManager, PreProcessor, DBManager, ModelManager, LLMManager, PipelineController
import argparse 
import schedule
import time

def main(args):
    env_manager = EnvManager(args)
    preprocessor = PreProcessor()
    db_manager = DBManager(env_manager.db_config)
    pipe = PipelineController(env_manager=env_manager, preprocessor=preprocessor, db_manager=db_manager)   
    pipe.set_env()
    
    poc_user_sql = """
        CREATE TABLE IF NOT EXISTS ibk_poc_user (
            user_id INTEGER PRIMARY KEY, -- 사용자 ID (1~10 고정)
            is_active BOOLEAN DEFAULT FALSE, -- 현재 사용 중 여부
            name VARCHAR(20) NOT NULL,
            company VARCHAR(10) NOT NULL
        );
    """

    poc_conf_sql = """
        CREATE TABLE IF NOT EXISTS ibk_poc_conf (
            conf_id BIGSERIAL PRIMARY KEY,  -- nextval 자동 설정
            title VARCHAR(100),
            start_time TIMESTAMP WITH TIME ZONE,
            end_time TIMESTAMP WITH TIME ZONE,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT FALSE,
            participant_count INTEGER DEFAULT 0,   -- is active 기준으로 체크 
            summary TEXT, 
            topic VARCHAR(100)
        );
    """

    poc_conference_log_sql = """
        CREATE TABLE IF NOT EXISTS ibk_poc_conf_log (
            conv_id BIGSERIAL PRIMARY KEY,  -- 자동 증가 Primary Key
            conf_id BIGSERIAL NOT NULL,    -- 회의 ID
            user_id INTEGER NOT NULL,   -- 사용자 ID
            content TEXT NOT NULL,   -- 로그 내용
            FOREIGN KEY (conf_id) REFERENCES ibk_poc_conf(conf_id) ON DELETE CASCADE,  -- conf_id 삭제 시 로그 삭제
            FOREIGN KEY (user_id) REFERENCES ibk_poc_user(user_id) ON DELETE CASCADE   -- user_id 삭제 시 로그 삭제
        );
    """

    pipe.postgres.db_connection.cur.execute(poc_user_sql)
    pipe.postgres.db_connection.cur.execute(poc_conf_sql)
    pipe.postgres.db_connection.cur.execute(poc_conference_log_sql)
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