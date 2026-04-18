# Verifeye: Agentic Forensic Auditor 🕵️‍♂️
**Built for OpenAI Codex Community Hackathon - Delhi**

Verifeye is an autonomous Agentic Auditor designed to detect "Revenue Leakage" in Indian SMEs. It uses GPT-4o-mini to cross-reference invoices against Master Service Agreements (MSAs) using a chain-of-thought agentic workflow.

## 🚀 Key Features
- **Agentic Skill-Calling:** Autonomously triggers `verify_gstin` and `calculate_tax_variance` tools.
- **Forensic Logs:** Real-time transparency into the agent's reasoning process.
- **Auto-Remediation:** Generates professional legal/financial recovery notices instantly.
- **Sleek UI:** High-fidelity dark-mode dashboard for CFO-level insights.

## 🛠 Tech Stack
- **Brain:** OpenAI GPT-4o-mini API
- **Logic:** Python (Agentic Framework)
- **Frontend:** Streamlit (Custom CSS)
- **Data:** JSON-based forensic datasets

## 🏃‍♂️ How to Run
1. Clone the repo.
2. Install dependencies: `pip install streamlit openai pandas`.
3. Set your API Key: `export OPENAI_API_KEY='your_key_here'`.
4. Run the app: `streamlit run app.py`.
