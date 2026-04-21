import os
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from engines.rag_engine import rag_engine
from engines.dsl_engine import dsl_engine
from db.firebase_manager import firebase_manager
from langchain_huggingface import HuggingFaceEmbeddings


class UniversalRAG:
    """
    MCP Orchestrator:
    - Tool 1: DSL Engine (Rule-based, structured logic, high precision)
    - Tool 2: MCP RAG Tool (Semantic retrieval using cosine similarity)
    """

    def __init__(self):
        llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            self.llm = Ollama(model=llm_model, base_url=base_url)
        except Exception:
            self.llm = None
            print("Warning: Could not connect to Ollama. Running in mock mode.")

        # MCP Agent Prompt
        self.fusion_prompt = PromptTemplate(
            input_variables=["history", "context_dsl", "context_rag", "query"],
            template='''
You are an advanced MCP (Model Context Protocol) Agent. 
Your intelligence is powered by two specialized tools.

TOOLS AVAILABLE:
1. DSL TOOL: Provides structured, rule-based data (VERIFY, WHEN, THEN). This is the "Source of Truth" for logic.
2. MCP RAG TOOL: Provides semantic context and documentation using high-precision cosine similarity.

RULES OF ENGAGEMENT:
- Use the DSL TOOL output for factual constraints, requirements, and logic-based verification.
- Use the MCP RAG TOOL output to provide context, explain concepts, and bridge gaps in the user's understanding.
- If the user asks a logic question ("When X happens..."), prioritize DSL.
- If the user asks a conceptual question ("What is..."), prioritize RAG.
- If the data is missing from BOTH tools, explicitly state: "I do not have the specific data in my current context."

<context_data>
DSL TOOL RESULT: {context_dsl}
MCP RAG TOOL RESULT: {context_rag}
</context_data>

<conversation_history>
{history}
</conversation_history>

User Question: {query}

Final Integrated Answer:
'''
        )

    def analyze_intent(self, query: str) -> str:
        """
        Router between DSL and MCP RAG tools.
        """
        query_upper = query.upper()
        dsl_keywords = ["VERIFY", "EVENT", "WHEN", "FOR", "THEN", "RULE", "REQUIREMENT"]

        has_dsl_signal = any(kw in query_upper for kw in dsl_keywords)

        if has_dsl_signal:
            if any(q_word in query.lower() for q_word in ["explain", "why", "how", "what"]):
                return "HYBRID"
            return "DSL"

        return "RAG"

    def execute_query(self, query: str, session_id: str, user_id: str) -> str:
        intent = self.analyze_intent(query)

        context_dsl = "N/A - Not requested for this intent."
        context_rag = "N/A - Not requested for this intent."

        # 📌 Fetch recent history (sliding window)
        history_records = firebase_manager.get_recent_queries(session_id, limit=5)
        history_text = "\n".join(
            [f"User: {h['question']}\nAI: {h['answer']}" for h in history_records]
        ) or "No prior history."

        # ⚙️ Execute tools
        if intent in ["DSL", "HYBRID"]:
            try:
                dsl_res = dsl_engine.execute_dsl(query)
                context_dsl = str(dsl_res)
            except Exception as e:
                context_dsl = f"DSL Error: {str(e)}"

        if intent in ["RAG", "HYBRID"]:
            try:
                context_rag = rag_engine.query(query)
            except Exception as e:
                context_rag = f"RAG Error: {str(e)}"

        # 🧠 LLM Fusion
        if self.llm:
            try:
                prompt_val = self.fusion_prompt.format(
                    history=history_text,
                    context_dsl=context_dsl,
                    context_rag=context_rag,
                    query=query
                )

                final_answer = self.llm.invoke(prompt_val)

            except Exception as e:
                final_answer = f"Orchestrator Error: {str(e)}"
        else:
            final_answer = (
                f"[Mock Mode] Intent: {intent} | "
                f"DSL: {context_dsl[:50]} | "
                f"RAG: {context_rag[:50]}"
            )

        # ☁️ ALWAYS log to Firebase (fixed issue)
        try:
            firebase_manager.log_query(user_id, session_id, query, final_answer)
        except Exception as e:
            print(f"Logging Error: {str(e)}")

        return final_answer


# 🚀 Initialize orchestrator
orchestrator = UniversalRAG()