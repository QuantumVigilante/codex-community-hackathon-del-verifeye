import json
import os
import time

import streamlit as st

from auditor_agent import audit_invoice, draft_remediation_email


st.set_page_config(page_title="Verifeye", layout="wide", initial_sidebar_state="expanded")


def load_json_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError:
        return None, f"Invalid JSON format in {path}"
    except OSError as exc:
        return None, f"Unable to read {path}: {exc}"


def find_matching_contract(invoice: dict, contracts: list):
    vendor_name = invoice.get("vendor_name")
    for contract in contracts:
        if contract.get("vendor_name") == vendor_name:
            return contract
    return None


def analyze_invoice_risk(invoice: dict, contract: dict):
    issues = []
    approved_rates = contract.get("approved_rates", {})
    standard_tax = float(contract.get("standard_tax_slab", 0.18) or 0.18)
    travel_cap = float(contract.get("travel_expense_cap", 0) or 0)

    for item in invoice.get("line_items", []):
        description = str(item.get("description", "Unknown Service"))
        hours = float(item.get("hours", 0) or 0)
        billed_rate = float(item.get("billed_rate", 0) or 0)
        billed_tax = float(item.get("tax_charged", 0) or 0)
        base_amount = round(hours * billed_rate, 2)
        expected_tax = round(base_amount * standard_tax, 2)

        if description == "Travel Expenses":
            if billed_rate > travel_cap:
                issues.append("Travel Cap Breach")
        else:
            approved_rate = approved_rates.get(description)
            if approved_rate is None:
                issues.append("Unapproved Service")
            elif billed_rate > float(approved_rate):
                issues.append("Rate Mismatch")

        if abs(billed_tax - expected_tax) > 0.01:
            issues.append("Tax Variance")

    unique_issues = sorted(set(issues))
    risk_level = "High" if unique_issues else "Low"
    trust_score = 96 if not unique_issues else max(40, 92 - (len(unique_issues) * 14))
    return {
        "issues": unique_issues,
        "risk_level": risk_level,
        "trust_score": trust_score,
    }


def render_metric_card(title: str, value: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_box(audit_result: dict):
    status = audit_result.get("status", "Fail")
    flags = audit_result.get("flags", [])
    recovery_action = audit_result.get("recovery_action", "Review manually.")
    border_color = "#00C853" if status == "Pass" else "#FF4B4B"
    glow_color = "rgba(0, 200, 83, 0.25)" if status == "Pass" else "rgba(255, 75, 75, 0.28)"

    if flags:
        flags_html = "".join(f"<li>{flag}</li>" for flag in flags)
    else:
        flags_html = "<li>No audit exceptions found.</li>"

    st.markdown(
        f"""
        <div class="result-box" style="border: 2px solid {border_color}; box-shadow: 0 0 28px {glow_color};">
            <div class="result-header">
                <span class="result-title">Audit Verdict</span>
                <span class="result-status" style="color: {border_color};">{status}</span>
            </div>
            <div class="result-section">
                <div class="result-subtitle">Flags</div>
                <ul class="result-list">{flags_html}</ul>
            </div>
            <div class="result-section">
                <div class="result-subtitle">Recovery Action</div>
                <div class="result-recovery">{recovery_action}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_email_composer(email_body: str):
    st.markdown(
        """
        <div class="composer-shell">
            <div class="composer-title">Vendor Notice Draft</div>
            <div class="composer-subtitle">Prepared by Verifeye for legal and finance review.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_area(
        "Drafted Email",
        value=email_body,
        height=320,
        key="drafted_email_view",
        label_visibility="collapsed",
    )
    st.button("Send to Vendor (Simulated)", disabled=True, use_container_width=True)


st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        [data-testid="stToolbar"] {display: none;}
        [data-testid="stDecoration"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}

        .stApp {
            background: radial-gradient(circle at top right, rgba(255, 75, 75, 0.08), transparent 25%),
                        radial-gradient(circle at bottom left, rgba(255, 165, 0, 0.10), transparent 25%),
                        #1A1A24;
            color: #FFFFFF;
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        section[data-testid="stSidebar"] {
            background: #15151E;
            border-right: 1px solid rgba(255, 75, 75, 0.18);
            min-width: 340px !important;
            max-width: 340px !important;
            visibility: visible !important;
            transform: none !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
        }

        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
        }

        h1, h2, h3, h4, h5, h6, p, label, div, span {
            color: #FFFFFF;
        }

        .app-shell {
            background: linear-gradient(180deg, rgba(37, 37, 53, 0.92), rgba(26, 26, 36, 0.96));
            border: 1px solid rgba(255, 75, 75, 0.12);
            border-radius: 18px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
            margin-bottom: 1.25rem;
        }

        .hero-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.3rem;
        }

        .hero-subtitle {
            color: #A0A0B0;
            font-size: 1rem;
            margin-bottom: 0;
        }

        .metric-card {
            background: linear-gradient(180deg, rgba(37, 37, 53, 0.98), rgba(29, 29, 42, 0.98));
            border: 1px solid rgba(255, 165, 0, 0.18);
            border-radius: 12px;
            padding: 1.15rem 1.1rem;
            min-height: 120px;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.26);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255, 75, 75, 0.10), transparent 50%, rgba(255, 165, 0, 0.08));
            pointer-events: none;
        }

        .metric-label {
            color: #A0A0B0;
            font-size: 0.92rem;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .metric-value {
            font-size: 1.7rem;
            font-weight: 750;
            line-height: 1.2;
        }

        .section-card {
            background: #252535;
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
            height: 100%;
        }

        .section-title {
            font-size: 1.02rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .section-caption {
            color: #A0A0B0;
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }

        .stCodeBlock, pre, code {
            background: #14141C !important;
            color: #F7F7F9 !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
        }

        .stSelectbox label, .stStatus label, .stRadio label {
            color: #FFFFFF !important;
        }

        div[data-baseweb="select"] > div {
            background: #252535 !important;
            border: 1px solid rgba(255, 75, 75, 0.26) !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            box-shadow: 0 0 0 1px transparent !important;
        }

        div[data-baseweb="select"] svg {
            fill: #FFA500 !important;
        }

        .stButton > button {
            width: 100%;
            background: linear-gradient(90deg, #FF4B4B 0%, #FFA500 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 12px;
            padding: 0.95rem 1.2rem;
            font-size: 1rem;
            font-weight: 800;
            box-shadow: 0 12px 30px rgba(255, 75, 75, 0.34);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 34px rgba(255, 75, 75, 0.40);
        }

        .stButton > button:focus {
            outline: none;
            box-shadow: 0 0 0 0.2rem rgba(255, 165, 0, 0.28);
        }

        .result-box {
            background: #252535;
            border-radius: 12px;
            padding: 1.15rem 1.2rem;
            margin-top: 1rem;
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .result-title {
            font-size: 1.1rem;
            font-weight: 800;
        }

        .result-status {
            font-size: 1.05rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .result-subtitle {
            font-size: 0.92rem;
            font-weight: 700;
            color: #A0A0B0;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .result-list {
            margin: 0 0 1rem 1.2rem;
            padding: 0;
            color: #FFFFFF;
        }

        .result-list li {
            margin-bottom: 0.45rem;
        }

        .result-recovery {
            color: #FFFFFF;
            font-size: 1rem;
        }

        [data-testid="stStatus"] {
            background: #252535;
            border: 1px solid rgba(255, 165, 0, 0.22);
            border-radius: 12px;
        }

        .sidebar-note {
            color: #A0A0B0;
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .sidebar-panel {
            background: linear-gradient(180deg, rgba(37, 37, 53, 0.94), rgba(29, 29, 42, 0.98));
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 0.95rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
        }

        .sidebar-panel-title {
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #A0A0B0;
            margin-bottom: 0.65rem;
            font-weight: 700;
        }

        .sidebar-kpi-row {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.45rem;
        }

        .sidebar-kpi {
            flex: 1;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 0.7rem;
        }

        .sidebar-kpi-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #A0A0B0;
            margin-bottom: 0.25rem;
        }

        .sidebar-kpi-value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #FFFFFF;
        }

        .status-chip {
            display: inline-block;
            background: rgba(0, 200, 83, 0.14);
            color: #8EF0B1;
            border: 1px solid rgba(0, 200, 83, 0.28);
            padding: 0.28rem 0.6rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            margin-top: 0.3rem;
        }

        .status-chip.warn {
            background: rgba(255, 165, 0, 0.14);
            color: #FFD089;
            border-color: rgba(255, 165, 0, 0.28);
        }

        .status-chip.error {
            background: rgba(255, 75, 75, 0.14);
            color: #FF9D9D;
            border-color: rgba(255, 75, 75, 0.28);
        }

        .plugin-list {
            display: grid;
            gap: 0.45rem;
        }

        .plugin-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 0.65rem 0.7rem;
            font-size: 0.88rem;
        }

        .plugin-state {
            float: right;
            color: #FFA500;
            font-weight: 700;
        }

        .plugin-state.ready {
            color: #7AE3A1;
        }

        .mini-note {
            color: #A0A0B0;
            font-size: 0.82rem;
            line-height: 1.5;
            margin-bottom: 0.32rem;
        }

        .composer-shell {
            background: linear-gradient(180deg, rgba(37, 37, 53, 0.98), rgba(29, 29, 42, 0.98));
            border: 1px solid rgba(255, 165, 0, 0.18);
            border-radius: 12px 12px 0 0;
            padding: 1rem 1rem 0.75rem 1rem;
            margin-top: 1rem;
        }

        .composer-title {
            font-size: 1.02rem;
            font-weight: 800;
            color: #FFFFFF;
            margin-bottom: 0.25rem;
        }

        .composer-subtitle {
            color: #A0A0B0;
            font-size: 0.9rem;
        }

        div[data-testid="stTextArea"] textarea {
            background: #14141C !important;
            color: #F7F7F9 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
            padding: 1rem !important;
            font-size: 0.95rem !important;
            line-height: 1.55 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="app-shell">
        <div class="hero-title">Verifeye</div>
        <div class="hero-subtitle">Agentic audit workspace for invoice-to-contract forensic validation.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


invoices, invoices_error = load_json_file("invoices.json")
contracts, contracts_error = load_json_file("contracts.json")

if invoices_error or contracts_error or not isinstance(invoices, list) or not isinstance(contracts, list):
    if invoices_error:
        st.error(invoices_error)
    if contracts_error:
        st.error(contracts_error)
    st.stop()


invoice_contract_pairs = []
for invoice in invoices:
    if not isinstance(invoice, dict):
        continue
    contract = find_matching_contract(invoice, contracts)
    if contract is None:
        continue
    risk_info = analyze_invoice_risk(invoice, contract)
    invoice_contract_pairs.append(
        {
            "invoice": invoice,
            "contract": contract,
            "risk_level": risk_info["risk_level"],
            "trust_score": risk_info["trust_score"],
            "issues": risk_info["issues"],
        }
    )

if not invoice_contract_pairs:
    st.error("No invoice and contract pairs are available for auditing.")
    st.stop()


vendor_options = sorted({pair["invoice"]["vendor_name"] for pair in invoice_contract_pairs})
openai_connected = bool(os.getenv("OPENAI_API_KEY"))
flagged_count = sum(1 for pair in invoice_contract_pairs if pair["risk_level"] == "High")

with st.sidebar:
    st.markdown("## Verifeye Control Panel")
    st.markdown(
        '<div class="sidebar-note">Filter the queue, inspect audit readiness, and jump straight to risky invoices without losing the current audit context.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="sidebar-panel">
            <div class="sidebar-panel-title">System Status</div>
            <div class="sidebar-kpi-row">
                <div class="sidebar-kpi">
                    <div class="sidebar-kpi-label">Invoices</div>
                    <div class="sidebar-kpi-value">{len(invoice_contract_pairs)}</div>
                </div>
                <div class="sidebar-kpi">
                    <div class="sidebar-kpi-label">Flagged</div>
                    <div class="sidebar-kpi-value">{flagged_count}</div>
                </div>
            </div>
            <div class="mini-note">OpenAI access</div>
            <div class="status-chip {'error' if not openai_connected else ''}">{'Connected' if openai_connected else 'Missing API Key'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_vendor = st.selectbox(
        "Vendor Filter",
        ["All Vendors"] + vendor_options,
        key="sidebar_vendor_filter",
    )
    selected_risk_filter = st.radio(
        "Risk Filter",
        ["All", "High", "Low"],
        horizontal=True,
        key="sidebar_risk_filter",
    )

    filtered_pairs = invoice_contract_pairs
    if selected_vendor != "All Vendors":
        filtered_pairs = [pair for pair in filtered_pairs if pair["invoice"]["vendor_name"] == selected_vendor]
    if selected_risk_filter != "All":
        filtered_pairs = [pair for pair in filtered_pairs if pair["risk_level"] == selected_risk_filter]

    if not filtered_pairs:
        st.warning("No invoices match the active filters.")
        st.stop()

    filtered_invoice_ids = [pair["invoice"]["invoice_id"] for pair in filtered_pairs]
    pending_invoice_selector = st.session_state.pop("pending_invoice_selector", None)
    if pending_invoice_selector in filtered_invoice_ids:
        st.session_state["invoice_selector"] = pending_invoice_selector
    if st.session_state.get("invoice_selector") not in filtered_invoice_ids:
        st.session_state["invoice_selector"] = filtered_invoice_ids[0]

    st.selectbox(
        "Invoice ID",
        filtered_invoice_ids,
        key="invoice_selector",
    )

    selected_pair = next(
        (pair for pair in filtered_pairs if pair["invoice"]["invoice_id"] == st.session_state["invoice_selector"]),
        filtered_pairs[0],
    )

    st.markdown(
        f"""
        <div class="sidebar-panel">
            <div class="sidebar-panel-title">Active Plugins</div>
            <div class="plugin-list">
                <div class="plugin-item">GSTIN Validator <span class="plugin-state ready">READY</span></div>
                <div class="plugin-item">Tax Variance Engine <span class="plugin-state ready">READY</span></div>
                <div class="plugin-item">Policy Checker <span class="plugin-state ready">READY</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_contract = selected_pair["contract"]
    selected_invoice = selected_pair["invoice"]
    issue_text = ", ".join(selected_pair["issues"]) if selected_pair["issues"] else "No predicted issues"
    chip_class = "warn" if selected_pair["risk_level"] == "High" else ""

    st.markdown(
        f"""
        <div class="sidebar-panel">
            <div class="sidebar-panel-title">Selection Intelligence</div>
            <div class="mini-note">Vendor: <strong>{selected_invoice['vendor_name']}</strong></div>
            <div class="mini-note">Invoice Date: <strong>{selected_invoice.get('date', 'N/A')}</strong></div>
            <div class="mini-note">Risk Profile</div>
            <div class="status-chip {chip_class}">{selected_pair['risk_level']}</div>
            <div class="mini-note" style="margin-top:0.55rem;">Trust score: <strong>{selected_pair['trust_score']}/100</strong></div>
            <div class="mini-note">Travel cap: <strong>INR {float(selected_contract.get('travel_expense_cap', 0) or 0):,.0f}</strong></div>
            <div class="mini-note">Service count: <strong>{len(selected_contract.get('approved_rates', {}))}</strong></div>
            <div class="mini-note">Predicted exceptions: <strong>{issue_text}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Quick Actions")
    if st.button("Jump to First Flagged", use_container_width=True):
        flagged_ids = [pair["invoice"]["invoice_id"] for pair in filtered_pairs if pair["risk_level"] == "High"]
        if flagged_ids:
            st.session_state["pending_invoice_selector"] = flagged_ids[0]
            st.rerun()

    if st.button("Clear Audit Output", use_container_width=True):
        st.session_state["audit_result"] = None
        st.session_state["drafted_email"] = ""
        st.rerun()


selected_pair = next(
    (pair for pair in invoice_contract_pairs if pair["invoice"]["invoice_id"] == st.session_state.get("invoice_selector")),
    None,
)

if selected_pair is None:
    st.error("Selected invoice could not be found.")
    st.stop()


selected_invoice = selected_pair["invoice"]
matching_contract = selected_pair["contract"]
selected_risk_level = selected_pair["risk_level"]
selected_trust_score = selected_pair["trust_score"]
selected_issues = selected_pair["issues"]

current_invoice_id = selected_invoice.get("invoice_id")
if st.session_state.get("active_invoice_id") != current_invoice_id:
    st.session_state["active_invoice_id"] = current_invoice_id
    st.session_state["audit_result"] = None
    st.session_state["drafted_email"] = ""


billed_amount = float(selected_invoice.get("total_billed_amount", 0) or 0)
vendor_name = selected_invoice.get("vendor_name", "Unknown Vendor")
standard_tax_slab = float(matching_contract.get("standard_tax_slab", 0) or 0)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

with metric_col_1:
    render_metric_card("Billed Amount", f"INR {billed_amount:,.2f}")

with metric_col_2:
    render_metric_card("Risk Level", selected_risk_level)

with metric_col_3:
    render_metric_card("Vendor Trust Score", f"{selected_trust_score}/100")


st.markdown(
    f"""
    <div class="section-card" style="margin-bottom: 1rem;">
        <div class="section-title">Audit Readiness</div>
        <div class="section-caption">Vendor: {vendor_name} | Standard Tax Slab: {standard_tax_slab * 100:.0f}% | Predicted issues: {', '.join(selected_issues) if selected_issues else 'None'}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Selected Invoice</div>
            <div class="section-caption">Raw invoice payload used by the audit agent.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(json.dumps(selected_invoice, indent=4), language="json")

with right_col:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Matching Contract</div>
            <div class="section-caption">Vendor MSA terms used for cross-reference checks.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(json.dumps(matching_contract, indent=4), language="json")


st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
run_audit = st.button("Run Agentic Audit", use_container_width=True)

if run_audit:
    with st.status("Running Verifeye Agent...", expanded=True) as status:
        st.write("Scanning MSA...")
        time.sleep(1)
        st.write("Parsing invoice line items...")
        time.sleep(1)
        st.write("Calling verify_gstin Plugin...")
        time.sleep(1)
        st.write("Computing tax variance checks...")
        time.sleep(1)
        st.write("Synthesizing audit verdict...")
        audit_result = audit_invoice(selected_invoice, matching_contract)
        time.sleep(0.5)
        status.update(label="Verifeye audit complete", state="complete", expanded=True)

    st.session_state["audit_result"] = audit_result
    st.session_state["drafted_email"] = ""


stored_audit_result = st.session_state.get("audit_result")
if stored_audit_result:
    render_result_box(stored_audit_result)

    if stored_audit_result.get("status") == "Fail":
        if st.button("Draft Vendor Notice", use_container_width=True):
            with st.spinner("Agent drafting legal notice..."):
                drafted_email = draft_remediation_email(
                    selected_invoice,
                    matching_contract,
                    stored_audit_result,
                )
                st.session_state["drafted_email"] = drafted_email

        drafted_email = st.session_state.get("drafted_email", "")
        if drafted_email:
            render_email_composer(drafted_email)
