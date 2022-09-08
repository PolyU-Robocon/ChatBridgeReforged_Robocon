"""
CBR config file stuffs
"""
import os
import shutil

from os import path
from ruamel import yaml
from typing import Any, List, Mapping
# from ruamel.yaml.comments import CommentedMap

from cbr.lib.logger import CBRLogger
from cbr.lib.typeddicts import TypedConfig, TypedConfigStruct
from cbr.lib.zip import Compressor

CHATBRIDGEREFORGED_VERSION = "0.2.5-dev030"
LIB_VERSION = "v20210915"
DEFAULT_CONFIG_PATH = "cbr/resources/default_config.yml"
CONFIG_PATH = "config.yml"
CONFIG_STRUCTURE: List[TypedConfigStruct] = [
    {'name': 'server_setting',
     'sub_structure': [
         {'name': 'host_name', 'sub_structure': [], },
         {'name': 'port', 'sub_structure': [], },
         {'name': 'aes_key', 'sub_structure': [], },
     ]
     },
    {'name': 'debug',
     'sub_structure': [
         {'name': 'all', 'sub_structure': [], },
         {'name': 'CBR', 'sub_structure': [], },
         {'name': 'plugin', 'sub_structure': [], },
     ]
     },
    {'name': 'clients', 'sub_structure': [], },
    {'name': 'log',
     'sub_structure': [
         {'name': 'size_to_zip', 'sub_structure': [], },
         {'name': 'split_log', 'sub_structure': [], },
         {'name': 'size_to_zip_chat', 'sub_structure': [], },
     ]
     }
]


class ConfigChecker:
    def __init__(self, logger: CBRLogger):
        self.logger = logger

    def check_all(self) -> TypedConfig:
        if not path.exists('config'):
            os.mkdir('config')
        if not path.exists('plugins'):
            os.mkdir('plugins')
        if not path.exists(CONFIG_PATH):
            self.logger.error("Config file is missing, default config generated")
            self.__gen_config()
        else:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config:
                data: TypedConfig = yaml.safe_load(config)
            try:
                self.logger.debug_config = data['debug']
                logs_data = data['log']
                split_log = logs_data['split_log']
                compressor = Compressor(self.logger)
                compressor.zip_log('latest.log', logs_data['size_to_zip'])
                self.logger.setup(split_log=split_log)
                if split_log:
                    compressor.zip_log('chat.log', logs_data['size_to_zip_chat'])
                    self.logger.setup(True)
            except KeyError:
                self.logger.setup()
                raise ValueError('Some config is missing in config.yml')
        self.logger.debug("Checking config ......", "CBR")
        self.__check_config_info(data)
        return data

    def __gen_config(self):
        if not path.exists(DEFAULT_CONFIG_PATH):
            raise FileNotFoundError('Default config not found, re-installing ChatBridgeReforged may fix the problem')
            # self.logger.bug()
        else:
            shutil.copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            self.logger.info("Default config is used now")
            self.logger.info("Please configure the config and restart again")
            self.logger.info("Exit now")
            exit(0)  # exit here

    def __check_config_info(self, data: Mapping[str, Any]):
        self.logger.debug('Checking config.yml', "CBR")
        if self.__check_node(data, CONFIG_STRUCTURE):
            self.logger.debug('Finish config check', "CBR")
        else:
            self.logger.setup()
            raise ValueError('Some config is missing in config.yml')

    def __check_node(self, data: Mapping[str, Any], structure: List[TypedConfigStruct], prefix: str = '') -> bool:
        check_node_result = True
        for struct in structure:
            name = struct['name']
            if name not in data:
                self.logger.error(f"Config '{prefix}{name}' is not exist in config.yml")
                check_node_result = False
                continue
            self.logger.debug(f"Checking for '{prefix}{name}'", "CBR")
            if 'sub_structure' in struct and len(struct['sub_structure']) != 0:
                flag = self.__check_node(data[name], struct['sub_structure'], f"{prefix}{name}.")
                check_node_result = check_node_result and flag
                continue
            if prefix == '' and name == 'clients':
                values = ', '.join([f"'{d['name']}'" for d in data[name]])
                self.logger.debug(f'Clients are: {values}', "CBR")
            else:
                self.logger.debug(f"Config '{prefix}{name}' values '{data[name]}'", "CBR")
        return check_node_result


class Config:
    def __init__(self, logger: CBRLogger):
        self.logger = logger
        self.version = CHATBRIDGEREFORGED_VERSION
        self.lib_version = LIB_VERSION
        self.config_checker = ConfigChecker(self.logger)
        self.raw_data = self.config_checker.check_all()
        try:
            self.ip = self.raw_data['server_setting']['host_name']
            self.port = self.raw_data['server_setting']['port']
            self.aes_key = self.raw_data['server_setting']['aes_key']
            self.debug = self.raw_data['debug']
            self.clients = self.raw_data['clients']
        except AttributeError:
            exit(0)
        self.logger.info(f"CBR is now starting at pid {os.getpid()}")
        self.logger.info(f'version : {self.version}, lib version : {self.lib_version}')
