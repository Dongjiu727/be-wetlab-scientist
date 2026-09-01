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

ASSAY_DISPLAY = {
    "western_blot": {"zh": "Western Blot", "en": "Western Blot"},
    "qpcr": {"zh": "qPCR", "en": "qPCR"},
}

UI_TEXT = {
    "zh": {
        "title": "🔬 Be a WetLab Scientist",
        "caption": "基于真实实验室troubleshooting经验的诊断助手 Demo",
        "step1": "1️⃣ 选择实验类型",
        "step2": "2️⃣ 你遇到的症状最接近下面哪一种？",
        "no_case": "该模块案例库暂未添加，敬请期待。",
        "restart": "🔄 重新开始",
        "diagnosis_label": "**可能原因：**",
        "confirm_label": "**建议的确认实验：**",
        "no_confirm": "（暂无补充建议）",
        "author_note": "📖 作者真实案例参考",
        "choose_branch": "选择最符合的情况：",
        "checklist_intro": "请逐条检查：",
        "checklist_done": "以上都已排查，仍无法解决 → 下一步",
        "next_step": "下一步 ➡️",
        "footer": (
            "💡 这是一个作品集Demo项目，诊断建议基于真实实验室经验整理，"
            "不能替代专业指导，具体问题建议结合实际情况判断。"
        ),
    },
    "en": {
        "title": "🔬 Be a WetLab Scientist",
        "caption": "A diagnostic assistant demo built from real lab troubleshooting experience",
        "step1": "1️⃣ Select the assay type",
        "step2": "2️⃣ Which symptom best matches what you're seeing?",
        "no_case": "No cases have been added for this module yet — stay tuned.",
        "restart": "🔄 Start over",
        "diagnosis_label": "**Likely cause:**",
        "confirm_label": "**Suggested confirmatory experiment:**",
        "no_confirm": "(no additional suggestion yet)",
        "author_note": "📖 Author's real case notes",
        "choose_branch": "Choose the option that best matches your situation:",
        "checklist_intro": "Please check each item:",
        "checklist_done": "All checked, still unresolved → Next step",
        "next_step": "Next ➡️",
        "footer": (
            "💡 This is a portfolio demo project. Diagnostic suggestions are compiled from "
            "real lab experience and are not a substitute for professional guidance — please "
            "use your judgment for your specific situation."
        ),
    },
}


def reset_session(entry_point: str):
    st.session_state.current_node = entry_point
    st.session_state.params = {}
    st.session_state.result = None


# ------- 语言选择（右上角） -------
if "lang" not in st.session_state:
    st.session_state.lang = "zh"

lang_col1, lang_col2 = st.columns([5, 1])
with lang_col2:
    lang_choice = st.selectbox(
        "🌐",
        options=["zh", "en"],
        format_func=lambda x: "中文" if x == "zh" else "English",
        index=["zh", "en"].index(st.session_state.lang),
        label_visibility="collapsed",
    )
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    st.rerun()

lang = st.session_state.lang
T = UI_TEXT[lang]

st.title(T["title"])
st.caption(T["caption"])

assay_type = st.selectbox(
    T["step1"],
    list(ASSAY_DISPLAY.keys()),
    format_func=lambda x: ASSAY_DISPLAY[x][lang],
)

engine = DiagnosticEngine(assay_type)
case_options = engine.get_case_list(lang)

if not case_options:
    st.warning(T["no_case"])
    st.stop()

case_id = st.selectbox(
    T["step2"],
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
    if st.button(T["restart"]):
        reset_session(case["entry_point"])
        st.rerun()

st.divider()

# ------- 已经得出诊断结果 -------
if st.session_state.get("result"):
    result = st.session_state.result
    st.success(f"{T['diagnosis_label']} {DiagnosticEngine.text(result, 'diagnosis', lang)}")
    confirm_text = DiagnosticEngine.text(result, "confirm_experiment", lang, default=T["no_confirm"])
    st.info(f"{T['confirm_label']} {confirm_text}")
    author_note = DiagnosticEngine.text(case, "author_case_note", lang)
    if author_note:
        with st.expander(T["author_note"]):
            st.write(author_note)
    st.stop()

# ------- 走到当前节点 -------
node_id = st.session_state.current_node
node = engine.get_node(case, node_id)

question_text = DiagnosticEngine.text(node, "question", lang)
if st.session_state.get("params"):
    try:
        question_text = question_text.format(**DiagnosticEngine.format_params(st.session_state.params, lang))
    except (KeyError, IndexError):
        pass

st.subheader(f"❓ {question_text}")

# checklist型节点（如抗体排查）
if node.get("is_checklist"):
    st.write(T["checklist_intro"])
    checklist_items = DiagnosticEngine.text_list(node, "checklist", lang)
    for item in checklist_items:
        st.checkbox(item, key=f"{node_id}_{item}")
    if st.button(T["checklist_done"]):
        st.session_state.current_node = node["on_all_ruled_out"]
        st.rerun()

# 分支型节点
elif "branches" in node:
    branch_labels = [DiagnosticEngine.text(b, "answer", lang) for b in node["branches"]]
    choice = st.radio(
        T["choose_branch"],
        branch_labels,
        key=f"radio_{node_id}",
        index=None,
    )
    if st.button(T["next_step"], disabled=(choice is None)):
        idx = branch_labels.index(choice)
        branch = node["branches"][idx]
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
st.caption(T["footer"])
