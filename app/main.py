"""
Be a WetLab Scientist —— 实验诊断助手 Demo
用法：streamlit run app/main.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from engine.diagnostic_engine import DiagnosticEngine  # noqa: E402

st.set_page_config(page_title="Be a WetLab Scientist", page_icon="🔬", layout="centered")

ASSAY_DISPLAY = {"western_blot": "Western Blot", "qpcr": "qPCR"}


def reset_session(entry_point: str):
    st.session_state.current_node = entry_point
    st.session_state.params = {}
    st.session_state.result = None


st.title("🔬 Be a WetLab Scientist")
st.caption("基于真实实验室troubleshooting经验的诊断助手 Demo")

assay_type = st.selectbox(
    "1️⃣ 选择实验类型",
    list(ASSAY_DISPLAY.keys()),
    format_func=lambda x: ASSAY_DISPLAY[x],
)

engine = DiagnosticEngine(assay_type)
case_options = engine.get_case_list()

if not case_options:
    st.warning("该模块案例库暂未添加，敬请期待。")
    st.stop()

case_id = st.selectbox(
    "2️⃣ 你遇到的症状最接近下面哪一种？",
    [c[0] for c in case_options],
    format_func=lambda cid: dict(case_options)[cid],
)

# case切换时重置会话状态
if st.session_state.get("current_case") != case_id:
    st.session_state.current_case = case_id
    case = engine.get_case(case_id)
    reset_session(case["entry_point"])

case = engine.get_case(case_id)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 重新开始"):
        reset_session(case["entry_point"])
        st.rerun()

st.divider()

# ------- 已经得出诊断结果 -------
if st.session_state.get("result"):
    result = st.session_state.result
    st.success(f"**可能原因：** {result['diagnosis']}")
    st.info(f"**建议的确认实验：** {result.get('confirm_experiment', '（暂无补充建议）')}")
    if case.get("author_case_note"):
        with st.expander("📖 作者真实案例参考"):
            st.write(case["author_case_note"])
    st.stop()

# ------- 走到当前节点 -------
node_id = st.session_state.current_node
node = engine.get_node(case, node_id)

question_text = node.get("question", "")
if st.session_state.get("params"):
    try:
        question_text = question_text.format(**st.session_state.params)
    except (KeyError, IndexError):
        pass

st.subheader(f"❓ {question_text}")

# checklist型节点（如抗体排查）
if node.get("is_checklist"):
    st.write("请逐条检查：")
    for item in node.get("checklist", []):
        st.checkbox(item, key=f"{node_id}_{item}")
    if st.button("以上都已排查，仍无法解决 → 下一步"):
        st.session_state.current_node = node["on_all_ruled_out"]
        st.rerun()

# 分支型节点
elif "branches" in node:
    choice = st.radio(
        "选择最符合的情况：",
        [b["answer"] for b in node["branches"]],
        key=f"radio_{node_id}",
        index=None,
    )
    if st.button("下一步 ➡️", disabled=(choice is None)):
        branch = next(b for b in node["branches"] if b["answer"] == choice)
        if "diagnosis" in branch:
            st.session_state.result = branch
        else:
            next_node, params = engine.resolve_next(branch)
            st.session_state.params.update(params)
            st.session_state.current_node = next_node
        st.rerun()

# 直接给出诊断的叶子节点（无分支）
elif "diagnosis" in node:
    st.session_state.result = node
    st.rerun()

st.divider()
st.caption(
    "💡 这是一个作品集Demo项目，诊断建议基于真实实验室经验整理，"
    "不能替代专业指导，具体问题建议结合实际情况判断。"
)
