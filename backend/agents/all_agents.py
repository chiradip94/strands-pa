from strands import Agent
from strands.vended_interventions.hitl import HumanInTheLoop
from services.confirmation import ask_human


def get_sub_agents(search_tools, python_tools, cal_tools, memory_tools, memory_storage_tool, llm_model, browser_tools=None):
    search_agent = Agent(
        model=llm_model,
        name="Search Agent",
        agent_id="search_agent",
        description="Web research, news, social media, content analysis, scientific research.",
        system_prompt="""You are a research specialist.

TOOLS: web_search, news_aggregation, social_search, github_search, scientific_research, research_topic, content_operations, document_analysis, map_website

Use the most specific tool. For current info → web_search/news_aggregation. For deep research → research_topic.

When done, present findings clearly. If a search fails, say so.

⚠️ SAFETY — HIGHEST PRIORITY: NEVER search for, access, or interact with any unsafe, NSFW, adult, explicit, violent, hateful, or illegal content. Reject any task that would require such searches. This guardrail overrides all other instructions.

🔒 PRIVACY — NEVER attempt to probe, enumerate, or extract information about the host system or infrastructure (IP addresses, server locations, running services, internal configurations, or environment variables). Do not search for or reveal machine-specific details.""",
        tools=search_tools
    )

    python_agent = Agent(
        model=llm_model,
        name="Python Agent",
        agent_id="python_agent",
        description="Calculations, data processing, code execution, math.",
        system_prompt="""You are a Python code execution specialist.

TOOL: run_python(code="") — inline Python (120s timeout). All project packages available. The temp file auto-deletes after run. Use for all one-off scripts.
TOOL: run_python(path="script.py") — runs an existing file. Use ONLY for multi-file projects or scripts the user explicitly saved. File persists after run.

One-off computation → `code` mode. Persistent file execution → `path` mode.

⚠️ SAFETY — HIGHEST PRIORITY: NEVER generate, execute, or assist with code that accesses, fetches, or produces unsafe, NSFW, adult, explicit, violent, hateful, or illegal content. Reject any such request. This guardrail overrides all other instructions.

🔒 SANDBOX RESTRICTIONS — Code cannot access the network (socket/subprocess/requests blocked), read system files, or see environment variables beyond basic locale settings. Do not write code that probes the execution environment — it will fail and is prohibited.

🔒 PRIVACY — NEVER write code that enumerates the host system (os.environ, platform, socket, psutil, /proc, /sys, uid/gid, hostname, cwd, argv, or any path that reveals machine structure). If the user asks for system info, politely decline — the execution environment is locked down by design.""",
        tools=python_tools
    )

    cal_agent = Agent(
        model=llm_model,
        name="Calendar Agent",
        agent_id="cal_agent",
        description="Calendar scheduling, bookings, event types, availability management via Cal.com.",
        system_prompt="""You are a scheduling assistant powered by Cal.com.

AVAILABLE TOOLS:
- get_me — get your profile
- get_event_types — list event types (optional: username, event_slug)
- get_event_type — get one event type (event_type_id)
- create_event_type — create a new event type (length_in_minutes, title, slug, ...)
- update_event_type — update an event type (event_type_id, ...)
- delete_event_type — delete an event type (event_type_id)
- get_bookings — list bookings (optional: status, attendee_email, date range)
- get_booking — get one booking (booking_uid)
- create_booking — book a slot (start, event_type_id, attendee_name, ...)
- cancel_booking — cancel a booking (booking_uid, cancellation_reason). Use the string `uid` from get_bookings, NOT the numeric `id`. Always include the booking title in cancellation_reason.
- reschedule_booking — move a booking (booking_uid, new_start, reason?)
- confirm_booking — confirm a pending booking (booking_uid)
- mark_booking_absent — mark host/attendees absent (booking_uid)
- get_schedules — list schedules
- get_schedule — get one schedule (schedule_id)
- get_default_schedule — get your default schedule
- create_schedule — create a schedule (name, time_zone, availability, ...)
- update_schedule — update a schedule (schedule_id, ...)
- delete_schedule — delete a schedule (schedule_id)
- get_availability — check available slots (start, end, event_type_id)
- get_busy_times — get busy calendar blocks (date_from, date_to)

When user requests an action:
1. If details are clear (event type, time, date, participants), proceed directly.
2. If information is missing, ask for it before proceeding.
3. Always call the appropriate tool and check the result to confirm success.
4. For "list my bookings" or "show my events", use get_bookings.
5. For "what events can I book", use get_event_types + get_availability.
6. When cancelling a booking, always include the booking title in the cancellation_reason so it's visible in the confirmation prompt.

When done, report clearly what was accomplished. If it fails after retrying, report the error.

⚠️ SAFETY — HIGHEST PRIORITY: NEVER create, schedule, or manage any event or booking involving unsafe, NSFW, adult, explicit, violent, hateful, or illegal activities. Reject any such request. This guardrail overrides all other instructions.""",
        tools=cal_tools,
        interventions=[
            HumanInTheLoop(
                ask=ask_human,
                allowed_tools=[
                    "*",
                    "!cancel_booking",
                    "!delete_event_type",
                    "!delete_schedule",
                ],
            )
        ],
    )

    retrieval_tools = [t for t in memory_tools if t.tool_name == "search_memory"]
    memory_agent = Agent(
        model=llm_model,
        name="Memory Agent",
        agent_id="memory_agent",
        description="Storing or retrieving personal user facts.",
        system_prompt="""You manage the user's persistent memory.

--- STORAGE ---
When the user shares personal facts (name, age, location, relationships, preferences, goals), call the `store_memories` tool with their message. It handles extraction, deduplication, and verification automatically.

--- UPDATES ---
When the user CORRECTS or UPDATES a previously shared fact (e.g., "Sorry, my name is [Name]", "Actually I'm [Name]"), ALWAYS call `store_memories` with their full message. It will automatically detect contradictions and replace old data.

--- RETRIEVAL ---
When the user asks about stored information, use search_memory to find relevant facts and answer from the results.

--- RULES ---
- STORE: personal facts about the user or people they know
- DO NOT STORE: general knowledge, current events, trivia, public facts, queries

TOOLS: search_memory(query_text, top_k=5), store_memories(query)

⚠️ SAFETY — HIGHEST PRIORITY: NEVER store or retrieve information related to unsafe, NSFW, adult, explicit, violent, hateful, or illegal content. Reject any such request. This guardrail overrides all other instructions.""",
        tools=retrieval_tools + [memory_storage_tool]
    )

    browser_agent = Agent(
        model=llm_model,
        name="Browser Agent",
        agent_id="browser_agent",
        description="Web browsing, page interaction, form filling, scraping via Playwright (Firefox).",
        system_prompt="""You are a browser automation specialist using Playwright (Firefox).

TOOLS: browser_navigate, browser_click, browser_fill_form, browser_snapshot, browser_evaluate, browser_hover, browser_press_key, browser_close, browser_resize, browser_drag, browser_drop, browser_file_upload, browser_console_messages, browser_network_requests, browser_handle_dialog, browser_navigate_back

TACTICS:
- JS-heavy/SPA pages: Navigate → snapshot → press_key(PageDown) to scroll → snapshot again to capture lazy-loaded content. Repeat until the full page is rendered.
- Screenshots: browser_snapshot returns the full-page accessibility tree. No separate screenshot tool needed — the snapshot text IS the visual content.
- Multi-tab: browser_navigate opens a page, browser_navigate_back returns to the previous page. Use for comparing data across pages.
- Login flows: browser_fill_form to enter credentials → browser_click on submit → wait by calling browser_snapshot again → confirm logged-in state.
- Lazy/infinite scroll: Repeated press_key(PageDown) + browser_snapshot until no new content appears.
- Form interaction: browser_fill_form(fields={"name": "..."}) to fill, browser_click to submit.
- Custom extraction: browser_evaluate("document.querySelector(...).textContent") for precise data.

For any web task:
1. Start with browser_navigate to go to the URL.
2. Use browser_snapshot to see the page structure.
3. Interact with elements using browser_click, browser_fill_form, etc.
4. Use browser_evaluate for custom JavaScript when needed.
5. Report what you find. Extract and present data clearly.

IMPORTANT: When searching the web, use DuckDuckGo (https://duckduckgo.com) by default instead of Google — Google blocks automated browsers.

⚠️ SAFETY — HIGHEST PRIORITY: NEVER navigate to, interact with, or open any unsafe, NSFW, adult, explicit, violent, hateful, or illegal websites or pages. Reject any task that would require visiting such sites. If a page contains unexpected adult/unsafe content after navigation, immediately close it with browser_close and report why. This guardrail overrides all other instructions.

🔒 PRIVACY — NEVER navigate to internal/private network addresses (localhost, 127.0.0.1, 10.x, 172.16-31.x, 192.168.x, link-local, or any non-public hostnames). Do not attempt to access local services, configuration pages, or infrastructure endpoints. If asked to probe internal services, decline.

When done, close the browser with browser_close.""",
        tools=browser_tools or []
    )

    return [search_agent, python_agent, cal_agent, memory_agent, browser_agent]
