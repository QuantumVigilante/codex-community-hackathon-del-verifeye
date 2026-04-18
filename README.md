Verifeye: Agentic Forensic Auditor 🕵️‍♂️
Submission for OpenAI Codex Community Hackathon - Delhi

Verifeye is an autonomous AI Agent designed to combat "Revenue Leakage" in Indian SMEs. By moving beyond static scripts to a truly Agentic Workflow, Verifeye cross-references unstructured invoice data against legal Master Service Agreements (MSAs) to identify financial discrepancies, tax non-compliance, and billing fraud.

🛑 The Problem
Indian mid-market firms lose 2-5% of annual revenue to manual billing errors and sophisticated vendor overcharges. Manual auditing is:

Slow: Taking days to cross-check line items against complex contracts.

Error-Prone: Missing subtle tax variance or unauthorized rate inflation.

Passive: Finding the error but leaving the "recovery" process to humans.

✅ The Solution: Verifeye
Verifeye doesn't just scan; it investigates. Built on GPT-4o, the agent uses a chain-of-thought process to autonomously decide which tools to use to validate an invoice's legitimacy.

🌟 Key Features
Agentic Reasoning: Real-time "Thought Traces" show the AI's internal logic as it audits line items.

Autonomous Skill-Calling: The agent calls specialized Python "Skills" (Plugins) for:

GSTIN Validation: Checking vendor legitimacy against simulated government records.

Tax Variance Engine: Calculating precise INR leakage from incorrect tax slabs.

Rate Card Parser: Detecting unauthorized price hikes per service category.

Auto-Remediation: Generates a professional, legally-sound demand letter for the CFO to reclaim lost funds instantly.

Sleek Forensic UI: A premium dark-mode dashboard designed for high-stakes financial environments.

🛠 Tech Stack
LLM: OpenAI GPT-4o (via Official Python SDK)

Backend: Python 3.10+

Frontend: Streamlit (Custom CSS-injected Dark Mode)

Data Handling: Pandas & JSON

Agent Architecture: Function Calling / Tool Selection

🚀 Getting Started
1. Prerequisites
Ensure you have an OpenAI API Key.

Bash
pip install streamlit openai pandas
2. Set Environment Variables
Bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-key-here"

# Mac/Linux/Bash
export OPENAI_API_KEY="your-key-here"
3. Run the Application
Bash
streamlit run app.py
📂 Project Structure
app.py: The high-fidelity dashboard and frontend logic.

auditor_agent.py: The "Brain"—OpenAI agentic workflow and tool-calling loop.

skills.py: Modular Python tools used by the Agent.

invoices.json & contracts.json: Forensic datasets with injected "fraud" scenarios for demo purposes.

👤 Author
Shubham Prasad
Delhi Technological University (DTU)
