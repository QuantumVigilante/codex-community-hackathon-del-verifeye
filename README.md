Verifeye: Agentic Forensic Auditor 🕵️‍♂️
Official Submission for the OpenAI Codex Community Hackathon – Delhi (2026)

Verifeye is an autonomous AI Agent designed to solve "Revenue Leakage" for Indian SMEs. By moving beyond static automation and into Agentic Reasoning, Verifeye cross-references unstructured invoice data against legal Master Service Agreements (MSAs) to identify financial discrepancies, tax non-compliance, and billing fraud in real-time.

🛑 The Problem: The "Invisible" Loss
Indian mid-market firms lose 2-5% of annual revenue to billing errors. Manual auditing is:

Slow: It takes days to cross-check line items against complex contracts.

Passive: Traditional tools find errors but don't act on them.

Fragmented: Verifying GSTINs and tax slabs usually requires manual switching between portals.

✅ The Solution: Verifeye Agentic Workflow
Verifeye doesn't just scan; it investigates. Built on OpenAI’s GPT-4o, the agent uses a chain-of-thought process to autonomously trigger specialized tools to validate an invoice's legitimacy.

🌟 Core Agentic Capabilities
Autonomous Skill-Calling: The agent intelligently calls modular Python tools (skills.py) to verify GSTINs and calculate tax variances.

Forensic Thought Traces: A live "Reasoning Stream" in the UI provides transparency into the agent's logic as it parses data.

Auto-Remediation Engine: Once a discrepancy is found, the agent autonomously drafts a professional, legally-sound demand letter for the vendor.

High-Fidelity Dashboard: A premium, dark-mode command center providing CFO-level insights at a glance.

🛠 Tech Stack
AI Engine: OpenAI GPT-4o (via Python SDK)

Framework: Python 3.10+

Interface: Streamlit (Custom CSS Dark Theme)

Data Analysis: Pandas & JSON Logic

Security: Environment-based API Key management

🚀 Quick Start
1. Installation
Bash
pip install streamlit openai pandas
2. Set Your Environment Variable
Bash
# Windows
set OPENAI_API_KEY="your-api-key-here"

# Mac/Linux
export OPENAI_API_KEY="your-api-key-here"
3. Launch the Auditor
Bash
streamlit run app.py
📂 Repository Structure
app.py: The forensic dashboard and frontend logic.

auditor_agent.py: The Agent Brain—handles tool calling and LLM chain-of-thought.

skills.py: Hardcoded forensic tools used by the Agent.

invoices.json & contracts.json: Structured datasets containing both "Clean" and "Fraudulent" scenarios.

👤 Project Lead
Shubham Prasad
3rd Year B.Tech, Computer Science Engineering
Delhi Technological University (DTU)
