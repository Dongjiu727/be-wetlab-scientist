"""
诊断引擎：assay类型无关的通用节点图遍历逻辑。
具体的诊断知识（案例、共享节点）都在 knowledge_base/ 下的YAML文件里，
这里只负责加载、合并、遍历——新增assay类型不需要改这个文件。
"""
import yaml
from pathlib import Path


class DiagnosticEngine:
    def __init__(self, assay_type: str, base_dir: str = "knowledge_base"):
        self.assay_type = assay_type
        self.base_dir = Path(base_dir) / assay_type
        self.shared_nodes = self._load_yaml("shared_nodes.yaml") or {}
        self.cases = self._load_yaml("cases.yaml") or []

    def _load_yaml(self, filename):
        path = self.base_dir / filename
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_case_list(self):
        """返回 [(case_id, symptom), ...] 供UI下拉选择"""
        return [(c["case_id"], c["symptom"]) for c in self.cases]

    def get_case(self, case_id):
        for c in self.cases:
            if c["case_id"] == case_id:
                return c
        raise KeyError(f"Case '{case_id}' not found for assay type '{self.assay_type}'.")

    def get_node(self, case: dict, node_id: str):
        """
        节点查找优先级：case专属节点 > 共享节点。
        这样case可以在必要时覆盖（override）某个共享节点的行为。
        """
        case_nodes = case.get("nodes") or {}
        if node_id in case_nodes:
            return case_nodes[node_id]
        if node_id in self.shared_nodes:
            return self.shared_nodes[node_id]
        raise KeyError(
            f"Node '{node_id}' not found in case '{case['case_id']}' "
            f"or shared_nodes.yaml for assay type '{self.assay_type}'."
        )

    @staticmethod
    def resolve_next(branch: dict):
        """
        branch['next'] 可能是字符串(node_id)，也可能是
        {"node": node_id, "params": {...}}（用于参数化子树，如node_antibody_problem）。
        返回统一的 (node_id, params) 元组。
        """
        nxt = branch.get("next")
        if nxt is None:
            return None, {}
        if isinstance(nxt, str):
            return nxt, {}
        return nxt.get("node"), nxt.get("params", {})
