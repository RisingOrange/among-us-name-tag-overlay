import configparser
import os

from pyinstaller_utils import executable_dir

def get_config():
    first_option = os.path.join(executable_dir(), 'my_config.ini')
    second_option = os.path.join(executable_dir(), 'config.ini')
    
    config = configparser.ConfigParser()
    if os.path.exists(first_option):
        config.read(first_option)
    elif os.path.exists(second_option):
        config.read(second_option)
    else:
        raise FileNotFoundError(f'no config-file found at {second_option}')
    config = config['DEFAULT']

    # check if the config file contains a token
    if config['DISCORD_TOKEN'] == 'YOUR_TOKEN':
        raise RuntimeError(f'Discord token is missing from config.ini')

    return config


if __name__ == '__main__':
    print(get_config()['DISCORD_TOKEN'])