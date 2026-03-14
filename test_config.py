import sys
sys.path.insert(0, '.')
from src.config_manager import ConfigManager
import logging
logging.basicConfig(level=logging.DEBUG)

config = ConfigManager()
print('Initial config:', config.get_all())
print('target_language:', config.get('target_language'))
config.set('target_language', 'en')
config.save()
print('Saved config:', config.get_all())
config2 = ConfigManager()
print('Reloaded target_language:', config2.get('target_language'))
assert config2.get('target_language') == 'en'
print('Config change persisted')
print('Config file:', config2.config_path)