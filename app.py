"""
Nonprofit Technology Advisor — Streamlit UI
Week 2 Assignment, Lonely Octopus AI Agent Bootcamp

Demonstrates: Context (org profile), Memory (persistent JSON), Tools (Anthropic tool_use)
Run: streamlit run app.py
"""

import json
import streamlit as st
from agent import run_agent, extract_memory, memory

# --- Page Config ---
st.set_page_config(
    page_title="MTM Nonprofit Tech Advisor",
    page_icon="🏛️",
    layout="wide",
)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    .mtm-header {
        background: linear-gradient(135deg, #0891b2 0%, #0e7490 50%, #155e75 100%);
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .mtm-header h1 {
        color: white;
        font-size: 28px;
        margin: 0;
        font-weight: 700;
    }
    .mtm-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 14px;
        margin: 4px 0 0 0;
    }
    .pillar-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin: 4px;
    }
    .pillar-context {
        background: #dcfce7;
        color: #166534;
    }
    .pillar-memory {
        background: #dbeafe;
        color: #1e40af;
    }
    .pillar-tools {
        background: #ffedd5;
        color: #9a3412;
    }
    .mtm-footer {
        text-align: center;
        color: #85abbd;
        font-size: 12px;
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #e5e7eb;
    }
    .mtm-footer a {
        color: #1ab1d2;
        text-decoration: none;
    }
    .tool-log {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session State Init ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "org_profile" not in st.session_state:
    st.session_state.org_profile = {}
if "advising_started" not in st.session_state:
    st.session_state.advising_started = False
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = {}

# --- Sidebar: Org Profile ---
with st.sidebar:
    st.image("mtm-logo.png", width=160)

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0891b2, #0e7490, #155e75);
                    padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <p style="color: white; font-weight: 600; font-size: 16px; margin: 0;">
                Organization Profile
            </p>
            <p style="color: rgba(255,255,255,0.8); font-size: 12px; margin: 4px 0 0 0;">
                Tell us about your nonprofit
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    org_name = st.text_input("Organization Name", placeholder="e.g., Hope Community Center")

    budget_tier = st.selectbox(
        "Annual Budget",
        ["", "Under $1M", "Under $5M", "$5M – $20M", "$20M – $100M", "Over $100M"],
    )

    staff_count = st.text_input("Staff Count", placeholder="e.g., 35")

    cause_area = st.selectbox(
        "Cause Area",
        [
            "",
            "Arts & Culture",
            "Community Services",
            "Education",
            "Environment",
            "Health & Human Services",
            "Housing & Homelessness",
            "International Development",
            "Social Justice & Advocacy",
            "Workforce Development",
            "Youth Development",
            "Other",
        ],
    )

    st.markdown(
        "**Current Tech Stack**  \n"
        '<span style="color: #64748b; font-size: 13px;">'
        "Select what's relevant to your pain points — no need to list everything</span>",
        unsafe_allow_html=True,
    )

    tech_options = {
        "Google Workspace": "Google Workspace (Gmail, Drive, Docs)",
        "Microsoft 365": "Microsoft 365 (Outlook, Teams, SharePoint)",
        "Salesforce": "Salesforce / Salesforce NPSP",
        "QuickBooks": "QuickBooks / Accounting software",
        "Spreadsheets": "Spreadsheets for tracking (Excel, Google Sheets)",
        "Mailchimp": "Mailchimp / Email marketing",
        "Zoom": "Zoom / Video conferencing",
        "Slack": "Slack / Team messaging",
        "WordPress": "WordPress / Website CMS",
        "Paper/manual": "Paper forms / Manual processes",
    }

    selected_tech = []
    cols = st.columns(2)
    for i, (key, label) in enumerate(tech_options.items()):
        with cols[i % 2]:
            if st.checkbox(label, key=f"tech_{key}"):
                selected_tech.append(key)

    other_tech = st.text_input(
        "Other tools (optional)",
        placeholder="e.g., Bloomerang, Asana, custom database",
    )
    current_tech = ", ".join(selected_tech)
    if other_tech.strip():
        current_tech = f"{current_tech}, {other_tech.strip()}" if current_tech else other_tech.strip()

    pain_points = st.text_area(
        "Top Technology Pain Points",
        placeholder="e.g., No CRM, manual donor tracking, security concerns",
        height=80,
    )

    it_capacity = st.selectbox(
        "IT Capacity",
        [
            "",
            "No dedicated IT staff",
            "One IT generalist",
            "Small IT team (2-5)",
            "Full IT department (5+)",
            "Using an MSP/outsourced IT",
        ],
    )

    st.markdown("---")

    start_button = st.button("Start Advising", type="primary", use_container_width=True)

    if start_button and org_name.strip():
        profile = {
            "org_name": org_name.strip(),
            "budget_tier": budget_tier,
            "staff_count": staff_count,
            "cause_area": cause_area,
            "current_tech": current_tech,
            "pain_points": pain_points,
            "it_capacity": it_capacity,
        }
        st.session_state.org_profile = profile
        st.session_state.advising_started = True
        st.session_state.messages = []
        st.session_state.tool_logs = {}

        # Initialize memory
        memory.init_org(org_name.strip(), profile)

        st.rerun()
    elif start_button:
        st.warning("Please enter an organization name.")

    # Pillars dashboard
    if st.session_state.advising_started:
        st.markdown("---")
        st.markdown("**Three Pillars**")

        profile = st.session_state.org_profile
        has_memory = memory.has_org(profile.get("org_name", ""))
        session_count = 0
        if has_memory:
            org_data = memory.get_org(profile["org_name"])
            session_count = org_data.get("session_count", 0) if org_data else 0

        tool_count = sum(len(v) for v in st.session_state.tool_logs.values())

        st.markdown(
            f'<span class="pillar-badge pillar-context">Context: {profile.get("org_name", "N/A")}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="pillar-badge pillar-memory">Memory: {"Session #" + str(session_count) if has_memory else "New org"}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="pillar-badge pillar-tools">Tools: {tool_count} calls</span>',
            unsafe_allow_html=True,
        )

    # Reset button
    if st.session_state.advising_started:
        st.markdown("---")
        if st.button("New Organization", use_container_width=True):
            st.session_state.advising_started = False
            st.session_state.messages = []
            st.session_state.org_profile = {}
            st.session_state.tool_logs = {}
            st.rerun()

# --- Main Area ---
st.image("mtm-logo.png", width=180)
st.markdown(
    """
    <div style="margin-top: -8px; margin-bottom: 24px;">
        <h1 style="color: #1c487b; font-size: 28px; margin: 0;">Nonprofit Technology Advisor</h1>
        <p style="color: #85abbd; font-size: 14px; margin: 4px 0 0 0;">
            Context-aware guidance powered by Claude &mdash;
            Week 2, Lonely Octopus AI Agent Bootcamp
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

if not st.session_state.advising_started:
    # Landing state
    st.markdown(
        """
        ### Welcome

        This advisor provides tailored technology guidance for nonprofit organizations.
        It demonstrates the **three pillars** of context-aware AI agents:

        | Pillar | What It Does |
        |--------|-------------|
        | **Context** | Your org profile shapes every recommendation |
        | **Memory** | Remembers past sessions — come back anytime |
        | **Tools** | Searches a curated knowledge base + Wikipedia |

        **Get started** by filling in your organization profile in the sidebar and clicking **Start Advising**.
        """
    )
else:
    profile = st.session_state.org_profile
    org_name = profile["org_name"]

    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show tool transparency for assistant messages
            if msg["role"] == "assistant" and i in st.session_state.tool_logs:
                tools_used = st.session_state.tool_logs[i]
                if tools_used:
                    with st.expander(f"What I used to answer this ({len(tools_used)} tool call{'s' if len(tools_used) != 1 else ''})"):
                        for t in tools_used:
                            st.markdown(f"**{t['tool']}**")
                            st.code(json.dumps(t["input"], indent=2), language="json")
                            if len(t["result"]) > 500:
                                st.markdown(f"*Result: {t['result'][:500]}...*")
                            else:
                                st.markdown(f"*Result: {t['result']}*")
                            st.markdown("---")

    # Auto-generate greeting on first load
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            with st.spinner("Preparing your personalized advisor..."):
                greeting_messages = [
                    {
                        "role": "user",
                        "content": (
                            "This is the start of a new advising session. "
                            "Please introduce yourself and acknowledge my organization's profile. "
                            "If you have memory of previous sessions, reference what we've discussed. "
                            "Then ask what technology challenges I'd like to focus on today."
                        ),
                    }
                ]
                response_text, tool_calls = run_agent(
                    greeting_messages, profile
                )
                st.markdown(response_text)

        # Store greeting
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        msg_idx = len(st.session_state.messages) - 1
        if tool_calls:
            st.session_state.tool_logs[msg_idx] = tool_calls

    # Chat input
    if user_input := st.chat_input("Ask about technology for your nonprofit..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build conversation for the API
        api_messages = []
        for msg in st.session_state.messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text, tool_calls = run_agent(
                    api_messages, profile
                )
                st.markdown(response_text)

                # Show tool transparency
                if tool_calls:
                    with st.expander(f"What I used to answer this ({len(tool_calls)} tool call{'s' if len(tool_calls) != 1 else ''})"):
                        for t in tool_calls:
                            st.markdown(f"**{t['tool']}**")
                            st.code(json.dumps(t["input"], indent=2), language="json")
                            if len(t["result"]) > 500:
                                st.markdown(f"*Result: {t['result'][:500]}...*")
                            else:
                                st.markdown(f"*Result: {t['result']}*")
                            st.markdown("---")

        # Store assistant response
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        msg_idx = len(st.session_state.messages) - 1
        if tool_calls:
            st.session_state.tool_logs[msg_idx] = tool_calls

        # Extract memory in background (best-effort)
        extract_memory(org_name, user_input, response_text)

# --- Footer ---
st.markdown(
    """
    <div class="mtm-footer">
        <a href="https://mtm.now" target="_blank">Meet the Moment</a> &mdash;
        Helping nonprofits harness technology to amplify their impact.
        <br>Built by Joshua Peskay | AI Agent Bootcamp, Mar 2026
    </div>
    """,
    unsafe_allow_html=True,
)
