from strands import Agent
from strands_google import use_google
from container import Container
from dependency_injector.wiring import Provide, inject

@inject
def get_agents(
    search_tools, 
    python_tools, 
    time_tools, 
    llm_model=Provide[Container.llm_model]
):
    # 1. Search Agent - Focused on research and information retrieval
    search_agent = Agent(
        model=llm_model,
        name="Search Agent",
        description="""
        You are a research specialist. You can search the web, news, social media, and more.
        Hand off to this agent when you need to find information that occurred after your training data.
        """,
        tools=search_tools
    )
    
    # 2. Python Agent - Focused on computation and logic
    python_agent = Agent(
        model=llm_model,
        name="Python Agent",
        description="""
        You are a computational specialist. You can execute Python code to perform calculations or data processing.
        Hand off to this agent for any task requiring math, data analysis, or script execution.
        """,
        tools=python_tools
    )

    # 3. Google Agent - Focused on Google services
    google_agent = Agent(
        model=llm_model,
        name="Google Agent",
        description="""
        You are a Google Assistant. You can manage Google Calendar events.
        Hand off to this agent when the user wants to schedule, list, or delete events.
        """,
        tools=[use_google]
    )

    # 4. Time Agent - Focused on current time
    time_agent = Agent(
        model=llm_model,
        name="Time Agent",
        description="""
        You are a time specialist. You can provide the current date and time.
        When asked for time, always fetch it for the 'Asia/Kolkata' timezone.
        if you need to add hours, minutes, etc, it may change the date.
        For example, if UTC is 2026-06-10 23:00:00, then it is +5:30 hours ahead, so it is 2026-06-11 04:30:00 in Asia/Kolkata.
        See how calculating the time in different timezones may change the date.
        This was just an example, use the current date and time.
        """,
        tools=time_tools
    )

    # 5. Initial Agent - The entry point for the swarm
    initial_agent = Agent(
        model=llm_model,
        name="Initial Agent",
        description="""
        You are the primary coordinator. Answer simple questions directly.
        For specialized tasks (Search, Python, Google, Time), hand off to the appropriate agent.
        """
    )
    
    return [search_agent, python_agent, google_agent, time_agent, initial_agent]