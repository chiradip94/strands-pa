from strands import Agent
from strands.session.repository_session_manager import RepositorySessionManager
from strands.vended_plugins.context_offloader import ContextOffloader, InMemoryStorage


def create_orchestrator(sub_agent_bundle, session_repo, llm_model, system_prompt, session_id):
    search_agent, python_agent, cal_agent, memory_agent, browser_agent, time_tools = sub_agent_bundle
    session_manager = RepositorySessionManager(
        session_id=session_id,
        session_repository=session_repo,
    )
    orchestrator = Agent(
        model=llm_model,
        name="Initial Agent",
        agent_id="initial_agent",
        system_prompt=system_prompt,
        tools=[
            search_agent.as_tool(
                name="search_agent",
                description="Web search and text-based research. CANNOT visit interactive websites, get live prices from booking/travel sites, render JavaScript pages, or interact with forms. For those, use browser_agent."
            ),
            python_agent.as_tool(
                name="python_agent",
                description="Calculations, data processing, code execution, math problems."
            ),
            cal_agent.as_tool(
                name="cal_agent",
                description="Calendar scheduling, bookings, event types, availability management."
            ),
            memory_agent.as_tool(
                name="memory_agent",
                description="Storing or retrieving personal user facts."
            ),
            browser_agent.as_tool(
                name="browser_agent",
                description="Visit and interact with live websites. Use for: getting live prices from booking/travel/hotel sites, JS-heavy SPAs, form filling, login flows, multi-tab research, scraping rendered content. This is the ONLY tool that can handle interactive websites."
            ),
        ] + time_tools,
        session_manager=session_manager,
        plugins=[ContextOffloader(storage=InMemoryStorage())],
    )
    return orchestrator
