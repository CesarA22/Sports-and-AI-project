"""
Tab Chat - interface do chatbot grounded + expander Auditoria.
"""
import streamlit as st
from src.chat.policy import check_policy
from src.chat.router import run_planner
from src.chat.tools import execute_tools
from src.chat.writer import run_writer
from src.chat.postcheck import check_response


OUT_OF_SCOPE_SUGGESTIONS = [
    "Quem são os top 10 por prospect_score nesta posição?",
    "Compare dois jogadores desta temporada.",
    "Explique a metodologia do projeto.",
]


def _refuse_message(reason: str) -> str:
    return f"**Não posso atender a essa solicitação.** {reason}\n\n**Sugestões de perguntas no escopo:**\n" + "\n".join(f"- {s}" for s in OUT_OF_SCOPE_SUGGESTIONS)


def render_chat_tab(data, context: dict):
    """Renderiza a tab Chat com input, histórico e Auditoria."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    # Sugestões baseadas nos filtros
    pos = context.get("position_group", "CM_AM")
    season = context.get("season_list", [2024])
    sug = [
        f"Top 10 por prospect_score em {pos} em {season}",
        f"Quem são os outliers em {pos}?",
        "Explique a metodologia do projeto.",
    ]
    st.markdown("### Chat (Grounded)")
    for s in sug:
        if st.button(s, key=f"sug_{hash(s) % 10**8}"):
            st.session_state.pending_query = s
            st.rerun()

    user_input = st.session_state.pop("pending_query", None)
    if user_input is None:
        user_input = st.chat_input("Pergunte sobre jogadores, clusters, metodologia...")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audit"):
                with st.expander("Auditoria"):
                    st.json(msg["audit"])

    if user_input:
        # Policy gate
        policy = check_policy(user_input)
        if not policy.allowed:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": _refuse_message(policy.reason), "audit": {"policy": "denied", "reason": policy.reason}})
            st.rerun()

        text = policy.sanitized_input or user_input
        st.session_state.messages.append({"role": "user", "content": text})

        # Planner
        ctx = {
            "season": context.get("season_list", [2024])[0] if context.get("season_list") else 2024,
            "position_group": context.get("position_group", "CM_AM"),
            "minutes_min": context.get("minutes_min", 600),
            "age_max": context.get("age_max", 23),
        }
        plan = run_planner(text, ctx)

        audit = {
            "intent": plan.get("intent"),
            "filters": plan.get("filters"),
            "entities": plan.get("entities"),
            "k": plan.get("k"),
        }

        if plan.get("intent") == "out_of_scope":
            reply = _refuse_message(plan.get("reason", "Fora do escopo."))
            audit["tools_called"] = []
            audit["evidence_rows"] = 0
            st.session_state.messages.append({"role": "assistant", "content": reply, "audit": audit})
            st.rerun()

        # Execute tools
        result = execute_tools(plan, data)
        evidence = result.get("evidence") or {}
        tools_called = result.get("tools_called", [])
        audit["tools_called"] = tools_called

        rows = 0
        for v in evidence.values():
            if isinstance(v, list):
                rows += len(v)
            elif isinstance(v, dict) and "error" not in str(v).lower():
                rows += 1
        audit["evidence_rows"] = rows
        audit["metrics_used"] = plan.get("metrics", [])

        # Answer writer
        reply = run_writer(text, plan, evidence)

        # Post-check
        ok, err = check_response(reply)
        if not ok:
            reply = run_writer(
                text,
                plan,
                evidence,
            )
            reply = reply + "\n\n*[Pós-checagem: inclua Fontes (dataset).]*"
            # Segundo retry com instrução extra - na prática o writer já deve incluir
            ok2, _ = check_response(reply)
            if not ok2:
                reply = "Não tenho dados no escopo do projeto para afirmar isso.\n\n**Fontes (dataset):** Nenhuma evidência suficiente."

        st.session_state.messages.append({"role": "assistant", "content": reply, "audit": audit})
        st.rerun()
