import os
import sys
from loguru import logger
import ujson
import yaml

output_path = 'output'
app_logs = f'{output_path}/logs.xml'

if not os.path.exists(output_path):
    os.makedirs(output_path)

logger.remove(0)
logger.add(sys.stderr, format="<level> {time:YYYY-MM-DD HH:mm:ss} | {level} | {message}</level>")
logger.add(app_logs, format="<level> {time:YYYY-MM-DD HH:mm:ss} | {level} | {message}</level>")

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except:
        logger.error("Unable to load configuration file. Check if it exists and is a valid yaml")
        sys.exit(1)

try:
    config_symbols = set(config['config']['symbols'])
    QTY_USDT = config['config']['qty-usdt']
    API_KEY = config['config']['apikey']
    API_SECRET = config['config']['apisecret']
    AUTHORIZATION = config['config']['login']
    WS = config['config']['ws']
except:
    logger.error("Invalid configuration options. Fix config and retry.")
    sys.exit(1)

if len(config_symbols) == 0:
    logger.error("No symbols configured. Fix config and retry.")
    sys.exit(1)

if QTY_USDT < 10:
    logger.error("Invalid qty-usdt. Make sure it's bigger than 10. Fix config and retry.")
    sys.exit(1)

if len(API_KEY) == 0 or len(API_SECRET) == 0 or len(AUTHORIZATION) == 0:
    logger.error("Invalid credentials in config file")
    sys.exit(1)

if len(WS) == 0:
    logger.error("Invalid WS server. Fix config and retry")
    sys.exit(1)
    
logger.info(f'Configured symbols {config_symbols}')

def check_stop_buy_file():
    return os.path.exists('stop.txt')

def get_env_var_bool(name: str, default_value: bool | None = None) -> bool:
    true_ = ('true', '1', 't')
    false_ = ('false', '0', 'f')
    value: str | None = os.getenv(name, None)
    if value is None:
        if default_value is None:
            raise ValueError(f'Variable `{name}` not set!')
        else:
            value = str(default_value)
    if value.lower() not in true_ + false_:
        raise ValueError(f'Invalid value `{value}` for variable `{name}`')
    return value in true_