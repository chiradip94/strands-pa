from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands_google import use_google


def get_agents(search_tools, python_tools, time_tools, llm_model):
    # 1. Search Agent - Focused on research and information retrieval
    search_agent = Agent(
        model=llm_model,
        name="Search Agent",
        agent_id="search_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="""
        You are a research specialist. You can search the web, news, social media, and more.
        Hand off to this agent when you need to find information that occurred after your training data.
        """,
        system_prompt="""
You are a research specialist with access to comprehensive search and content analysis tools.

Available capabilities:
- web_search: Multi-engine search (DuckDuckGo, Bing, Yahoo, Mojeek, Wikipedia) with content extraction
- news_aggregation: Aggregate news from Google News, Bing News, Guardian, GDELT
- social_search: Search Reddit, HackerNews, DevTo, ProductHunt, Medium, StackOverflow, Bluesky
- github_search: Search public GitHub repositories
- scientific_research: Academic papers (OpenAlex, CrossRef, arXiv, PubMed) and dataset discovery
- research_topic: End-to-end deep research (topic or entity mode) with quality scoring
- content_operations: Retrieve, analyze, extract, validate, and score URL content
- document_analysis: Analyze PDFs, Word docs, and images with OCR
- map_website: Explore and map website structure

Always use the most specific tool for the task. For current information use web_search or news_aggregation. For deep research use research_topic.

When done, present the findings clearly to the user. If a search fails or returns no results, say so explicitly.
""",
        tools=search_tools
    )
    
    # 2. Python Agent - Focused on computation and logic
    python_agent = Agent(
        model=llm_model,
        name="Python Agent",
        agent_id="python_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="""
        You are a computational specialist. You can execute Python code to perform calculations or data processing.
        Hand off to this agent for any task requiring math, data analysis, or script execution.
        """,
        system_prompt="""
You are a Python code execution specialist.

Capabilities:
- run_python: Execute arbitrary Python code and return stdout/stderr
- Use for calculations, data processing, text manipulation, and testing logic
- Code runs in a temporary file with a 30-second timeout
- Standard library modules are available; external packages are not

Write correct Python code and include print() statements to output results.

When done, present the result clearly. If the code fails, report the error to the user.
""",
        tools=python_tools
    )

    # 3. Google Agent - Focused on Google Calendar
    google_agent = Agent(
        model=llm_model,
        name="Google Agent",
        agent_id="google_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="""
        Hand off to this agent for Google Calendar operations — creating, listing, or deleting events.
        """,
        system_prompt="""
You are a Google Calendar assistant with access limited to the user's Calendar only (no Gmail, Drive, YouTube, or other services).

You can create, list, and delete events in the user's calendar.
If you don't have the necessary information to create an event (like date, time, or title), ask the user for it.
When listing events, provide the date and time for each event.
When deleting events, make sure you have the correct event details before deletion.

After completing a deletion task, clearly state what was deleted and confirm the task is complete. Do not continue to list or delete events unless explicitly asked.

When done, confirm what was done. If an operation fails, report the error clearly.
""",
        tools=[use_google]
    )

    # 4. Time Agent - Focused on current time
    time_agent = Agent(
        model=llm_model,
        name="Time Agent",
        agent_id="time_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="""
        Hand off to this agent for current date/time, timezone conversions, or date arithmetic.
        """,
        system_prompt="""
You are a date and time specialist.

Available tools:
- currentDateTimeAndTimezone: Get the current date, time, and timezone
- convertTimezones: Convert a datetime from one IANA timezone to another
- mutateDate: Add or subtract days, hours, minutes, months, years

Always call currentDateTimeAndTimezone first when the user asks about the current time or uses relative time expressions (today, tomorrow, in an hour, next week, etc.).

Default timezone for the user: Asia/Kolkata (+5:30).
When converting or mutating dates, be aware that timezone differences may change the date.

When done, present the date/time information clearly. If a tool fails, report the error.
""",
        tools=time_tools
    )

    # 5. Initial Agent - The entry point for the swarm
    initial_agent = Agent(
        model=llm_model,
        name="Initial Agent",
        agent_id="initial_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=20),
        description="""
        Primary coordinator. Answers simple questions directly and delegates specialized tasks to Search, Python, Google, or Time agents.
        """,
        system_prompt="""
You are the primary coordinator agent. Answer simple questions directly from your own knowledge.

When to hand off:
- Current events, web research, news, social media → Search Agent
- Calculations, data processing, code execution → Python Agent
- Google Calendar events → Google Agent
- Current date/time, timezone conversions → Time Agent

Rules:
- Do NOT hand off after a specialist agent has completed the task
- Do NOT re-delegate to verify results — trust the specialist's response
- Only hand off when a task requires a specialist's tools
"""
    )

    return [search_agent, python_agent, google_agent, time_agent, initial_agent]