from utils.log_utils import *
import hashlib
import json
from datetime import datetime
from elasticsearch import Elasticsearch, NotFoundError
import time
import traceback


class Paras:

    @staticmethod
    def date_str():
        return current_time()[:10]

    # GitHub
    github_pat = os.getenv('GITHUB_PAT')
    organization_slugs = os.getenv('ORGANIZATION_SLUGS')

    # ElasticSearch
    primary_key = os.getenv('PRIMARY_KEY', 'unique_hash')
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    # Log path
    log_path = os.getenv('LOG_PATH', 'logs')

    @staticmethod
    def get_log_path():
        return os.path.join(Paras.log_path, Paras.date_str())

    # Execution interval HOURS
    execution_interval = int(os.getenv('EXECUTION_INTERVAL', 6))


logger = configure_logger(log_path=Paras.log_path)
logger.info('-----------------Starting-----------------')


class Indexes:
    index_completions = os.getenv('INDEX_COMPLETIONS', 'copilot_completions')
    index_chat = os.getenv('INDEX_CHAT', 'copilot_chat')
    index_extension = os.getenv('INDEX_EXTENSION', 'copilot_extension')


def generate_unique_hash(data, key_properties=[]):
    key_string = '-'.join([data.get(key_propertie) for key_propertie in key_properties])
    unique_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return unique_hash


class DataSplitter:
    def __init__(self, data, additional_properties={}):
        self.data = data
        self.additional_properties = additional_properties
        self.correction_for_0 = 0

    def __get_total_list(self):
        total_list = []
        logger.info(f"Generating total list from data")
        
        day = self.data.get('day')
        total_chat_turns = self.data.get('total_chat_turns', 0)
        total_completions_count = self.data.get('total_completions_count', 0)
        total_extension_count = self.data.get('total_extension_count', 0)
        
        total_data = {
            'day': day,
            'total_chat_turns': self.correction_for_0 if total_chat_turns == 0 else total_chat_turns,
            'total_completions_count': self.correction_for_0 if total_completions_count == 0 else total_completions_count,
            'total_extension_count': self.correction_for_0 if total_extension_count == 0 else total_extension_count
        }
        
        # 添加额外属性
        total_data.update(self.additional_properties)
        
        # 生成唯一哈希
        total_data['unique_hash'] = generate_unique_hash(
            total_data, 
            key_properties=['day']
        )
        
        total_list.append(total_data)
        return total_list

    def get_completions_list(self):
        completions_list = []
        logger.info(f"Generating completions list from data")
        
        day = self.data.get('day')
        usage_data = self.data.get('usage', {})
        
        for username, user_data in usage_data.items():
            # 处理completions数据
            completions_data = user_data.get('completions', {})
            for editor_version, editor_data in completions_data.items():
                for model_name, model_data in editor_data.get('models', {}).items():
                    for language, count in model_data.get('languages', {}).items():
                        completions_entry = {
                            'day': day,
                            'username': username,
                            'editor': editor_version,
                            'model': model_name,
                            'language': language,
                            'count': count
                        }
                        
                        # 添加额外属性
                        completions_entry.update(self.additional_properties)
                        
                        # 生成唯一哈希
                        completions_entry['unique_hash'] = generate_unique_hash(
                            completions_entry, 
                            key_properties=['day', 'username', 'editor', 'model', 'language']
                        )
                        
                        completions_list.append(completions_entry)
        
        return completions_list

    def get_chat_list(self):
        chat_list = []
        logger.info(f"Generating chat list from data")
        
        day = self.data.get('day')
        usage_data = self.data.get('usage', {})
        
        for username, user_data in usage_data.items():
            # 处理chat数据
            chat_data = user_data.get('chat', {})
            for chat_type, chat_type_data in chat_data.items():
                editor_versions = chat_type_data.get('editor_version', {})
                for editor_version, editor_data in editor_versions.items():
                    for model_name, count in editor_data.get('models', {}).items():
                        chat_entry = {
                            'day': day,
                            'username': username,
                            'chat_type': chat_type,
                            'editor': editor_version,
                            'model': model_name,
                            'count': count
                        }
                        
                        # 添加额外属性
                        chat_entry.update(self.additional_properties)
                        
                        # 生成唯一哈希
                        chat_entry['unique_hash'] = generate_unique_hash(
                            chat_entry,
                            key_properties=['day', 'username', 'chat_type', 'editor', 'model']
                        )
                        
                        chat_list.append(chat_entry)
        
        return chat_list
        
    def get_extension_list(self):
        extension_list = []
        logger.info(f"Generating extension list from data")
        
        day = self.data.get('day')
        usage_data = self.data.get('usage', {})
        
        for username, user_data in usage_data.items():
            # 处理extension数据
            extension_data = user_data.get('extension', {})
            for extension_name, extension_info in extension_data.items():
                editor_versions = extension_info.get('editor_version', {})
                for editor_version, editor_data in editor_versions.items():
                    for model_name, count in editor_data.get('models', {}).items():
                        extension_entry = {
                            'day': day,
                            'username': username,
                            'extension': extension_name,
                            'editor': editor_version,
                            'model': model_name,
                            'count': count
                        }
                        
                        # 添加额外属性
                        extension_entry.update(self.additional_properties)
                        
                        # 生成唯一哈希
                        extension_entry['unique_hash'] = generate_unique_hash(
                            extension_entry,
                            key_properties=['day', 'username', 'extension', 'editor', 'model']
                        )
                        
                        extension_list.append(extension_entry)
        
        return extension_list



class ElasticsearchManager:

    def __init__(self, primary_key=Paras.primary_key):
        self.primary_key = primary_key
        self.es = Elasticsearch(
            Paras.elasticsearch_url
        )
        self.check_and_create_indexes()

    # Check if all indexes in the indexes are present, and if they don't, they are created based on the files in the mapping folder
    def check_and_create_indexes(self):
        for index_name in Indexes.__dict__:
            if index_name.startswith('index_'):
                index_name = Indexes.__dict__[index_name]
                if not self.es.indices.exists(index=index_name):
                    mapping_file = f'mapping/{index_name}_mapping.json'
                    with open(mapping_file, 'r') as f:
                        mapping = json.load(f)
                    self.es.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")

    def write_to_es(self, index_name, data):
        last_updated_at = current_time()
        data['last_updated_at'] = last_updated_at
        doc_id = data.get(self.primary_key)
        logger.info(f"Writing data to Elasticsearch index: {index_name}")
        try:
            self.es.get(index=index_name, id=doc_id)
            self.es.update(index=index_name, id=doc_id, doc=data)
            logger.info(f'[updated] to [{index_name}]: {data}')
        except NotFoundError:
            self.es.index(index=index_name, id=doc_id, document=data)
            logger.info(f'[created] to [{index_name}]: {data}') 


def main():
    logger.info(f"==========================================================================================================")

    # Define the path to the metrics file
    today_date = datetime.now().strftime('%Y-%m-%d')
    metrics_file_path = os.path.join("auditlogs", 'metrics', f'copilot-usage_{today_date}.json')

    # Read the metrics file
    try:
        with open(metrics_file_path, 'r') as file:
            data = json.load(file)
            logger.info(f"Successfully read metrics file: {metrics_file_path}")
    except FileNotFoundError:
        logger.error(f"Metrics file not found: {metrics_file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {metrics_file_path}")
        return

    es_manager = ElasticsearchManager()

    # Initialize DataSplitter and process the data
    data_splitter = DataSplitter(data)
    completions_list = data_splitter.get_completions_list()
    chat_list = data_splitter.get_chat_list()
    extension_list = data_splitter.get_extension_list()

    # Write to ES
    for data in completions_list:
        es_manager.write_to_es(Indexes.index_completions, data)
    
    for data in chat_list:
        es_manager.write_to_es(Indexes.index_name_breakdown, data)

    for data in extension_list:
        es_manager.write_to_es(Indexes.index_name_breakdown_chat, data)
    
    logger.info(f"Data processing completed successfully.")


if __name__ == "__main__":
    while True:
        try:
            main()
            logger.info(f"Sleeping for {Paras.execution_interval} hours before next execution...")
            for _ in range(Paras.execution_interval * 3600 // 3600):
                logger.info("Heartbeat: still running...")
                time.sleep(3600)
        except Exception as e:
            logger.error(f"An error occurred: {traceback.format_exc(e)}")
            time.sleep(5)
        finally:
            logger.info('-----------------Finished-----------------')
