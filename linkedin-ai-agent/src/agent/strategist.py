"""
Content Strategist Agent

ReAct-based agent that autonomously decides what content to create.
"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from dotenv import load_dotenv

from .memory.database import Database
from .memory.learner import InsightLearner
from .tools.trends import fetch_trends_tool, get_all_trends_tool
from .tools.repos import list_repos_tool, analyze_repo_tool, compare_repos_tool
from .tools.matching import match_trends_tool, search_code_tool, find_best_content_match
from .tools.history import (
    get_post_history_tool,
    get_insights_tool,
    get_last_post_reasoning_tool,
    suggest_next_post_tool
)
from .tools.publisher import generate_post_tool, generate_post_with_insights_tool

load_dotenv()


# ReAct prompt template
REACT_PROMPT = """You are a Content Strategist Agent for LinkedIn. Your goal is to help developers create engaging LinkedIn posts about their code.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (must be valid JSON or simple string)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important guidelines:
1. Always check trends first to find relevant topics
2. Compare repos to find the best content opportunity
3. Use insights from past performance to optimize
4. Generate posts that connect code to trends
5. Keep the user's chat_id: {chat_id} for all operations

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class ContentStrategist:
    """
    ReAct agent that strategically decides what LinkedIn content to create.

    Capabilities:
    - Analyzes multiple repos to find best content
    - Matches code to current trends
    - Learns from engagement metrics
    - Generates optimized posts
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_iterations: int = 10,
        verbose: bool = False
    ):
        """
        Initialize the content strategist agent.

        Args:
            model: OpenAI model to use
            temperature: LLM temperature (lower = more focused)
            max_iterations: Maximum reasoning steps
            verbose: Whether to print reasoning steps
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.max_iterations = int(os.getenv("AGENT_MAX_ITERATIONS", max_iterations))
        self.verbose = verbose

        self.db = Database()
        self.learner = InsightLearner(self.db)

        # Initialize tools
        self.tools = self._create_tools()

        # Create prompt
        self.prompt = PromptTemplate(
            template=REACT_PROMPT,
            input_variables=["input", "chat_id", "agent_scratchpad", "tools", "tool_names"]
        )

    def _create_tools(self) -> list[Tool]:
        """Create the list of tools available to the agent."""
        return [
            # Trend tools
            fetch_trends_tool,
            get_all_trends_tool,

            # Repo tools
            list_repos_tool,
            analyze_repo_tool,
            compare_repos_tool,

            # Matching tools
            match_trends_tool,
            search_code_tool,
            find_best_content_match,

            # History tools
            get_post_history_tool,
            get_insights_tool,
            get_last_post_reasoning_tool,
            suggest_next_post_tool,

            # Publisher tools
            generate_post_tool,
            generate_post_with_insights_tool,
        ]

    def _create_agent(self, chat_id: str) -> AgentExecutor:
        """Create an agent executor for a specific chat."""
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt.partial(chat_id=chat_id)
        )

        # Create executor with limits
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

    def run(self, chat_id: str, task: str) -> dict:
        """
        Run the agent with a specific task.

        Args:
            chat_id: User's Telegram chat ID
            task: What to do (e.g., "generate a post", "find trending content")

        Returns:
            Dict with 'output' (final answer) and 'reasoning' (steps taken)
        """
        agent = self._create_agent(chat_id)

        try:
            result = agent.invoke({"input": task})

            # Extract reasoning from intermediate steps
            reasoning = []
            for step in result.get("intermediate_steps", []):
                action = step[0]
                observation = step[1]
                reasoning.append({
                    "tool": action.tool,
                    "input": str(action.tool_input),
                    "output": str(observation)[:200] + "..." if len(str(observation)) > 200 else str(observation)
                })

            return {
                "output": result["output"],
                "reasoning": reasoning,
                "success": True
            }

        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "reasoning": [],
                "success": False
            }

    def generate_daily_post(self, chat_id: str) -> dict:
        """
        Generate the daily LinkedIn post.

        This is the main entry point for the daily cron job.
        The agent will:
        1. Check current trends
        2. Analyze connected repos
        3. Find the best content opportunity
        4. Generate an optimized post

        Args:
            chat_id: User's Telegram chat ID

        Returns:
            Dict with generated post and reasoning
        """
        task = """Generate a LinkedIn post for today. Follow these steps:
1. First, fetch current developer trends from HackerNews
2. List the user's connected repositories
3. Compare the repos to find which has the best content potential
4. Match trends to the best repo's code
5. Get insights from past post performance
6. Generate an optimized post using all this information

Return the generated post."""

        return self.run(chat_id, task)

    def explain_last_post(self, chat_id: str) -> dict:
        """
        Explain why the last post was generated the way it was.

        Args:
            chat_id: User's Telegram chat ID

        Returns:
            Explanation of content decisions
        """
        task = "Explain the reasoning behind the last generated post. What repo was chosen and why? What trend was matched? What insights were applied?"

        return self.run(chat_id, task)

    def get_content_suggestions(self, chat_id: str) -> dict:
        """
        Get suggestions for what to post about.

        Args:
            chat_id: User's Telegram chat ID

        Returns:
            Content suggestions based on trends and history
        """
        task = """Provide content suggestions for the user. Do the following:
1. Check current trends
2. Look at what content has performed well historically
3. Analyze connected repos for interesting content
4. Suggest 2-3 potential post topics with reasons"""

        return self.run(chat_id, task)


# Convenience functions for direct use
def generate_post(chat_id: str, verbose: bool = False) -> dict:
    """Generate a daily post for a user."""
    agent = ContentStrategist(verbose=verbose)
    return agent.generate_daily_post(chat_id)


def explain_post(chat_id: str) -> dict:
    """Explain the last post's reasoning."""
    agent = ContentStrategist()
    return agent.explain_last_post(chat_id)


def get_suggestions(chat_id: str) -> dict:
    """Get content suggestions."""
    agent = ContentStrategist()
    return agent.get_content_suggestions(chat_id)


if __name__ == "__main__":
    # Test the agent
    import sys

    chat_id = sys.argv[1] if len(sys.argv) > 1 else "test_user"

    print(f"Testing Content Strategist Agent for chat_id: {chat_id}")
    print("=" * 50)

    agent = ContentStrategist(verbose=True)
    result = agent.generate_daily_post(chat_id)

    print("\n" + "=" * 50)
    print("RESULT:")
    print(result["output"])

    if result["reasoning"]:
        print("\nREASONING STEPS:")
        for i, step in enumerate(result["reasoning"], 1):
            print(f"{i}. {step['tool']}: {step['output'][:100]}...")
