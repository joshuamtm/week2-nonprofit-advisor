"""
Nonprofit Technology Advisor — Streamlit UI
Week 2 Assignment, Lonely Octopus AI Agent Bootcamp

Demonstrates: Context (org profile), Memory (persistent JSON), Tools (Anthropic tool_use)
Run: streamlit run app.py
"""

import json

import streamlit as st
from agent import run_agent, extract_memory, memory
from export import generate_docx
from session_io import serialize_session, parse_session

# --- Page Config ---
st.set_page_config(
    page_title="MTM Nonprofit Tech Advisor",
    page_icon="favicon.png",
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
        "ChatGPT": "ChatGPT (OpenAI)",
        "Microsoft Copilot": "Microsoft Copilot",
        "Google Gemini": "Google Gemini",
        "Claude": "Claude (Anthropic)",
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

    st.markdown(
        "**IT Support**  \n"
        '<span style="color: #64748b; font-size: 13px;">'
        "Select all that apply</span>",
        unsafe_allow_html=True,
    )

    it_options = {
        "No dedicated IT staff": "No dedicated IT staff",
        "IT generalist": "Internal IT generalist",
        "IT team": "Internal IT team (2+)",
        "MSP": "Outsourced IT / MSP",
        "Fractional CIO/CTO": "Fractional / Virtual CIO or CTO",
        "Fractional CISO": "Fractional / Virtual CISO",
        "Fractional CAIO": "Fractional / Virtual Chief AI Officer",
        "IT-savvy staff": "Non-IT staff handle tech informally",
    }

    selected_it = []
    it_cols = st.columns(2)
    for i, (key, label) in enumerate(it_options.items()):
        with it_cols[i % 2]:
            if st.checkbox(label, key=f"it_{key}"):
                selected_it.append(key)

    it_capacity = ", ".join(selected_it) if selected_it else ""

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

    # Save session + reset
    if st.session_state.advising_started:
        st.markdown("---")

        # Export session
        if st.session_state.messages:
            st.markdown("**Save Your Advice**")

            profile = st.session_state.org_profile
            docx_bytes = generate_docx(st.session_state.messages, profile)
            org_slug = profile.get("org_name", "session").lower().replace(" ", "-")

            st.download_button(
                label="Download as Word Doc",
                data=docx_bytes,
                file_name=f"mtm-advice-{org_slug}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

            # Save session for resuming later
            st.markdown("**Resume Later**")
            session_md = serialize_session(profile, st.session_state.messages)

            st.download_button(
                label="Save Session (.md)",
                data=session_md.encode("utf-8"),
                file_name=f"mtm-session-{org_slug}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Download this file to resume your session later. Upload it on the home page to continue.",
            )

        st.markdown("---")
        if st.button("New Organization", use_container_width=True):
            st.session_state.advising_started = False
            st.session_state.messages = []
            st.session_state.org_profile = {}
            st.session_state.tool_logs = {}
            st.rerun()

# --- Main Area ---
st.image("mtm-logo.png", width=280)
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
    # Resume session option
    st.markdown(
        """
        <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;
                    padding: 16px; margin-bottom: 24px;">
            <p style="font-weight: 600; color: #0e7490; margin: 0 0 4px 0;">
                Returning? Resume a previous session
            </p>
            <p style="color: #64748b; font-size: 13px; margin: 0;">
                Upload a saved session file (.md) to pick up where you left off.
                Your organization profile and conversation history will be restored.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload a saved session file",
        type=["md"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        try:
            markdown_text = uploaded_file.read().decode("utf-8")
            restored_profile, restored_messages = parse_session(markdown_text)

            if restored_profile.get("org_name"):
                st.session_state.org_profile = restored_profile
                st.session_state.messages = restored_messages
                st.session_state.advising_started = True
                st.session_state.tool_logs = {}
                st.session_state["_just_resumed"] = True
                st.rerun()
            else:
                st.error("Could not find an organization profile in this file. Please check the file format.")
        except Exception:
            st.error("Could not parse this file. Please upload a valid saved session (.md) file.")

    st.markdown("")

    # Landing state — two audience tabs
    tab_users, tab_bootcamp = st.tabs(["For Nonprofit Staff", "For Bootcamp Reviewers"])

    with tab_users:
        st.markdown(
            """
            ### Your AI Technology Advisor

            Get **free, tailored technology guidance** for your nonprofit — powered by
            AI and informed by Meet the Moment's 30+ years of nonprofit technology experience.

            **How it works:**
            1. Fill in your organization's profile in the sidebar (name, budget, staff, pain points)
            2. Click **Start Advising** to meet your AI advisor
            3. Ask any technology question — CRM selection, cybersecurity, cloud migration,
               AI adoption, budgeting, and more
            4. Get recommendations calibrated to your budget, team size, and technical capacity

            **What makes it useful:**
            - Advice is personalized to *your* organization, not generic
            - It remembers your full conversation during a session, so you can ask follow-up questions and build on earlier answers
            - Every answer shows what sources were used, so you can see the reasoning
            - It recommends nonprofit-specific discounts and programs (TechSoup, Microsoft Nonprofit, Google for Nonprofits)
            - **Download your advice** as a Word document, or **save your session** as a markdown file to resume later
            - Upload a saved session file anytime to pick up where you left off — no account needed

            **This is an AI advisor, not a human.** It's designed to give you a helpful starting
            point for technology decisions, not replace professional consulting. Always validate
            recommendations with your team before making major changes.

            ---

            ### Privacy & Data

            **What's safe to enter:**
            - Your organization name, budget range, staff count, and cause area
            - General technology pain points (e.g., "we need a CRM" or "our security is weak")
            - Questions about tools, platforms, and best practices

            **What you should NOT enter:**
            - Passwords, API keys, or login credentials
            - Personally identifiable information (names, SSNs, donor lists, client records)
            - Financial details (bank accounts, credit card numbers, specific grant amounts)
            - Protected health information (PHI) or sensitive client data

            **What happens to your data:**
            - **Nothing is saved on our servers.** When you close or refresh the page, your session is erased from memory. We do not store your conversation, your org profile, or any information you enter.
            - **You control your data.** You can optionally download a session file (.md) to your own device to resume later. This file stays on your computer — we never see it.
            - Your questions are sent to Anthropic's Claude AI to generate responses. Anthropic's [usage policy](https://www.anthropic.com/policies) applies — conversations through the API are not used to train their models.
            - No analytics, no tracking, no cookies beyond what Streamlit requires to run.

            **Bottom line:** You can safely use your real organization name and general details. Just don't paste in anything you'd be uncomfortable sharing in a public setting.

            ---

            **We'd love your feedback!** Try it out and let us know what's helpful and what could
            be better: [joshua@mtm.now](mailto:joshua@mtm.now)

            *Built by [Meet the Moment](https://mtm.now) — helping nonprofits harness technology to amplify their impact.*
            """
        )

    with tab_bootcamp:
        st.markdown(
            """
            ### Week 2 Assignment — Context, Memory, and Tools

            This is a **context-aware nonprofit technology advisor** built for Week 2 of
            The Lonely Octopus AI Agent Bootcamp. It evolves the Week 1 single-turn Task
            Generator into a multi-turn agent with tool use, persistent memory, and
            organization-aware context.

            **The Three Pillars:**

            | Pillar | Implementation |
            |--------|---------------|
            | **Context** | Sidebar org profile injected into every system prompt — change the budget tier and the same question gives different advice |
            | **Memory** | JSON-backed persistence keyed by org name — maintains full conversation context within a session; users can save/resume sessions via downloadable markdown files (stateless, privacy-preserving) |
            | **Tools** | Two Anthropic `tool_use` tools: `search_knowledge_base` (22 curated nonprofit tech entries, budget-filtered) and `fetch_wikipedia_summary` (REST API with search fallback) |

            **Architecture:**
            - `agent.py` — Agentic tool-use loop (call Claude → execute tools → loop until `end_turn`)
            - `tools.py` — Tool definitions + execution functions
            - `memory.py` — `MemoryManager` class with JSON persistence
            - `knowledge_base.json` — 22 curated entries covering CRM, security, AI, cloud, etc.
            - `session_io.py` — Markdown-based session save/resume (stateless persistence)
            - `app.py` — Streamlit UI with sidebar profile, chat, pillars dashboard, tool transparency

            **Key demo moments:**
            1. Fill in an org profile → agent greets with context-aware intro
            2. Ask "What CRM should we use?" → triggers `search_knowledge_base`
            3. Ask "What is NIST?" → triggers `fetch_wikipedia_summary`
            4. Close browser, reopen, same org name → memory persists
            5. Change budget tier → same question gives different advice
            6. Save session → download .md → refresh page → upload .md → conversation resumes

            **Stack:** Python, Anthropic SDK (Claude Sonnet + Haiku), Streamlit, Wikipedia REST API
            """
        )

    st.markdown("")
    st.markdown("**Get started** by filling in your organization profile in the sidebar and clicking **Start Advising**.")
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

    # Auto-generate greeting on first load (skip if resuming with existing messages)
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            with st.spinner("Preparing your personalized advisor..."):
                greeting_messages = [
                    {
                        "role": "user",
                        "content": (
                            "This is the start of a new advising session. "
                            "Please introduce yourself briefly as a personalized AI technology advisor "
                            "from Meet the Moment, acknowledge my organization's profile, "
                            "and then suggest 3-5 specific technology challenges I might want to "
                            "tackle today based on my profile and pain points. Present them as a "
                            "numbered list I can pick from, while noting I can also ask about anything else."
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
    elif st.session_state.get("_just_resumed"):
        # Show a resume notice once
        del st.session_state["_just_resumed"]
        st.info(
            f"Session resumed for **{org_name}** with "
            f"{len(st.session_state.messages)} previous messages. "
            f"Continue the conversation below."
        )

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
