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
        logger.error("Unable to log configuration file. Check if it exists and is a valid yaml")
        sys.exit(1)

try:
    config_symbols = set(config['config']['symbols'])
    QTY_USDT = config['config']['qty-usdt']
    API_KEY = config['config']['apikey']
    API_SECRET = config['config']['apisecret']
    AUTHORIZATION = config['config']['login']
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
    logger.error("Invalid credentials")
    sys.exit(1)
    
logger.info(f'Configured symbols {config_symbols}')


def load_status():
    status_file = f'{output_path}/status.json'
    try:
        with open(status_file, 'r') as f:
            return ujson.load(f)
    except FileNotFoundError:
        return {}

def save_status(status):
    status_file = f'{output_path}/status.json'
    with open(status_file, 'w') as f:
        ujson.dump(status, f)


def check_stop_buy_file():
    return os.path.exists('stop.txt')

def check_stop_buy_allow_dca_file():
    return os.path.exists('stop_allow_dca.txt')
