from tronpy import Tron
from tronpy.providers import HTTPProvider
from utils.logger import logger
import time

class BlockWatcher:
    def __init__(self, rpc_nodes):
        self.rpc_nodes = rpc_nodes
        self.current_node_index = 0
        self.client = self._init_client()

    def _init_client(self):
        node_url = self.rpc_nodes[self.current_node_index]
        logger.info(f"正在初始化 Tron 客户端: {node_url}")
        return Tron(HTTPProvider(node_url))

    def _switch_node(self):
        self.current_node_index = (self.current_node_index + 1) % len(self.rpc_nodes)
        node_url = self.rpc_nodes[self.current_node_index]
        logger.warning(f"由于异常，正在切换到节点: {node_url}")
        self.client = Tron(HTTPProvider(node_url))

    def get_latest_block_number(self):
        while True:
            try:
                return self.client.get_latest_block_number()
            except Exception as e:
                logger.error(f"获取最新区块高度失败: {e}")
                self._switch_node()
                time.sleep(1)

    def get_block(self, block_num):
        while True:
            try:
                # get_block 支持传入区块号
                return self.client.get_block(block_num)
            except Exception as e:
                logger.error(f"获取区块 {block_num} 详情失败: {e}")
                self._switch_node()
                time.sleep(1)
