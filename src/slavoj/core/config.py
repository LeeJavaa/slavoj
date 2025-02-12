from dataclasses import dataclass
from typing import Optional
import yaml
import os
from pathlib import Path

@dataclass
class TwilioConfig:
    account_sid: str
    auth_token: str
    phone_number: str

@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: str
    max_tokens: int
    temperature: float

@dataclass
class MongoDBConfig:
    connection_string: str
    database: str

@dataclass
class ProcessingConfig:
    max_concurrent_books: int
    response_timeout: int
    aggregation_timeout: int

@dataclass
class AppConfig:
    twilio: TwilioConfig
    llm: LLMConfig
    mongodb: MongoDBConfig
    processing: ProcessingConfig
    environment: str
    log_level: str

class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv('CONFIG_PATH', 'config.dev.yaml')

    def load_config(self) -> AppConfig:
        """Load configuration from YAML file and environment variables."""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Load configurations with environment variable fallbacks
        twilio_config = TwilioConfig(
            account_sid=os.getenv('TWILIO_ACCOUNT_SID', config_data['twilio']['account_sid']),
            auth_token=os.getenv('TWILIO_AUTH_TOKEN', config_data['twilio']['auth_token']),
            phone_number=os.getenv('TWILIO_PHONE_NUMBER', config_data['twilio']['phone_number'])
        )

        llm_config = LLMConfig(
            provider=os.getenv('LLM_PROVIDER', config_data['llm']['provider']),
            api_key=os.getenv('LLM_API_KEY', config_data['llm']['api_key']),
            model=os.getenv('LLM_MODEL', config_data['llm']['model']),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', config_data['llm']['max_tokens'])),
            temperature=float(os.getenv('LLM_TEMPERATURE', config_data['llm']['temperature']))
        )

        mongodb_config = MongoDBConfig(
            connection_string=os.getenv('MONGODB_CONNECTION_STRING',
                                      config_data['mongodb']['connection_string']),
            database=os.getenv('MONGODB_DATABASE', config_data['mongodb']['database'])
        )

        processing_config = ProcessingConfig(
            max_concurrent_books=int(os.getenv('MAX_CONCURRENT_BOOKS',
                                             config_data['processing']['max_concurrent_books'])),
            response_timeout=int(os.getenv('RESPONSE_TIMEOUT',
                                         config_data['processing']['response_timeout'])),
            aggregation_timeout=int(os.getenv('AGGREGATION_TIMEOUT',
                                            config_data['processing']['aggregation_timeout']))
        )

        return AppConfig(
            twilio=twilio_config,
            llm=llm_config,
            mongodb=mongodb_config,
            processing=processing_config,
            environment=os.getenv('APP_ENVIRONMENT', 'development'),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
