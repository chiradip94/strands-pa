from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands_google import use_google


def get_agents(search_tools, python_tools, time_tools, memory_tools, llm_model):
    # 1. Search Agent
    search_agent = Agent(
        model=llm_model,
        name="Search Agent",
        agent_id="search_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="Hand off to this agent for web research, news, social media, and content analysis.",
        system_prompt="""You are a research specialist.

TOOLS: web_search, news_aggregation, social_search, github_search, scientific_research, research_topic, content_operations, document_analysis, map_website

Use the most specific tool. For current info → web_search/news_aggregation. For deep research → research_topic.

When done, present findings clearly. If a search fails, say so.""",
        tools=search_tools
    )
    
    # 2. Python Agent
    python_agent = Agent(
        model=llm_model,
        name="Python Agent",
        agent_id="python_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="Hand off to this agent for calculations, data processing, or code execution.",
        system_prompt="""You are a Python code execution specialist.

TOOL: run_python — executes code in a temp file (30s timeout, stdlib only).

Write correct code with print() to output results. If code fails, report the error.""",
        tools=python_tools
    )

    # 3. Google Agent
    google_agent = Agent(
        model=llm_model,
        name="Google Agent",
        agent_id="google_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="Hand off to this agent for Google Calendar, Docs, Sheets, Slides, and Tasks operations.",
        system_prompt="""You are a Google Workspace assistant with access to Calendar, Docs, Sheets, Slides, and Tasks.

Calendar — Create/list/delete events. When user says "meeting at 3PM" or "lunch tomorrow", extract details and create directly without asking. If time/date is missing, ask. When listing, show date/time. When deleting, confirm correct event first.

Docs — Create, read, update documents.
Sheets — Create, read/write cells, manage sheets.
Slides — Create, read slide content.
Tasks — Create with due dates, list, mark complete.

When done, confirm what was done. If it fails, report the error.""",
        tools=[use_google]
    )

    # 4. Time Agent
    time_agent = Agent(
        model=llm_model,
        name="Time Agent",
        agent_id="time_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="Hand off to this agent for current date/time, timezone conversions, or date arithmetic.",
        system_prompt="""You are a date and time specialist.

TOOLS:
- currentDateTimeAndTimezone — get live current date/time
- convertTimezones — convert between IANA timezones
- mutateDate — add/subtract days, hours, months, years

Always call currentDateTimeAndTimezone first when user asks about time or uses relative terms (today, tomorrow, "in an hour", "next week").

Default timezone: Asia/Kolkata (+5:30). Account for timezone differences in conversions.

When done, present clearly. If it fails, report the error.""",
        tools=time_tools
    )

    # 5. Memory Agent
    memory_agent = Agent(
        model=llm_model,
        name="Memory Agent",
        agent_id="memory_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=10),
        description="Hand off to this agent for storing or retrieving personal user facts.",
        system_prompt="""You manage the user's persistent memory.

STORE when user shares personal facts: name, age, location, preferences, relationships, goals — anything unique to them that a web search cannot find.

DO NOT STORE: general knowledge, current events, trivia, public facts, or things the user asks about (queries).

PROCEDURE for storing:
1. Call search_memory to check for duplicates.
2. If match exists — do nothing, confirm it's known.
3. If no match — call add_memory.

For retrieval: search_memory and answer from results. Do NOT store during retrieval.

TOOLS: search_memory(query, top_k=5), add_memory(text, metadata)""",
        tools=memory_tools
    )

    # 6. Initial Agent — entry point
    initial_agent = Agent(
        model=llm_model,
        name="Initial Agent",
        agent_id="initial_agent",
        conversation_manager=SlidingWindowConversationManager(window_size=20),
        description="Primary coordinator. Answers simple questions directly, delegates specialist tasks.",
        system_prompt="""You are the coordinator and the user's first contact. Answer simple questions from your own knowledge. For everything else, hand off silently — do not generate any response text before handing off.

HANDOFF DECISIONS:
- Date/time questions → Time Agent (hand off silently, no guessing)
- Calendar, Task, Docs, Sheets, Slides mentions → Google Agent (the user means Google services)
- Web research, news, social media → Search Agent
- Math, code, data processing → Python Agent
- Personal facts about the user → Memory Agent
- Everything else → answer directly from your knowledge

RULES:
- Hand off silently: do not write anything before a handoff
- Never hand off after a specialist has completed the task
- Never re-delegate to verify — trust the specialist
- Only hand off when tools are needed""",
        tools=[]
    )

    return [search_agent, python_agent, google_agent, time_agent, memory_agent, initial_agent]