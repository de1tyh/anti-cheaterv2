import json
import os
import threading
from utils.logger import logger

class StateManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lock = threading.Lock()
        self.state = self._load_state()

    def _load_state(self):
        if not os.path.exists(self.file_path):
            initial_state = {
                "last_block": 0,
                "processed_txs": []
            }
            self._save_to_file(initial_state)
            return initial_state
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
            return {"last_block": 0, "processed_txs": []}

    def _save_to_file(self, state):
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")

    def get_last_block(self):
        return self.state.get("last_block", 0)

    def update_last_block(self, block_num):
        with self.lock:
            self.state["last_block"] = block_num
            self._save_to_file(self.state)

    def is_tx_processed(self, tx_id):
        return tx_id in self.state.get("processed_txs", [])

    def add_processed_tx(self, tx_id):
        with self.lock:
            if "processed_txs" not in self.state:
                self.state["processed_txs"] = []
            
            self.state["processed_txs"].append(tx_id)
            
            # 限制去重列表长度，防止文件过大 (保留最近1000个)
            if len(self.state["processed_txs"]) > 1000:
                self.state["processed_txs"] = self.state["processed_txs"][-1000:]
                
            self._save_to_file(self.state)
