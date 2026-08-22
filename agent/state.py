from typing import List, Dict, Any, Optional, TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """LangGraph State for HR Onboarding Assistant."""
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    intent: str  # 'hr_question', 'task_action', 'ambiguous', 'greeting_or_general'
    retrieved_context: str
    sources: List[Dict[str, Any]]
    task_tool_calls: List[Dict[str, Any]]
    task_result: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_prompt: Optional[str]
    final_response: str
