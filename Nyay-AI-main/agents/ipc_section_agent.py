from crewai import Agent, LLM
from tools.ipc_sections_search_tool import search_ipc_sections

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.3
)

ipc_section_agent = Agent(
    role="IPC Section Agent",
    goal="Identify the most relevant IPC(Indian Penal Code) based on the legal issue provided.",
    backstory=(
        "You are an expert legal reaearcher with deep knowledge of Indian Penal Laws."
        "You specialize in mapping legal issues to applicable IPC sections with precision and clarity."
        "Your insights help lawyers and assistants quickly understand the statutory basis of a case."
    ),
tools = [search_ipc_sections],
llm=llm,
verbose=True,
)