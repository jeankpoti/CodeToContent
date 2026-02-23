"""
LinkedIn Post Generator

Generates LinkedIn posts from code context using LangChain and OpenAI.
"""

import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()


class PostGenerator:
    """Generates LinkedIn posts from code context."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the post generator.

        Args:
            model: OpenAI model to use
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.system_prompt = """You are a Senior Technical Evangelist who writes engaging LinkedIn posts about code and software development.

Your posts are:
- Authentic and conversational (not robotic or overly formal)
- Educational but accessible to a broad developer audience
- Include relevant code snippets when they add value
- Use line breaks for readability
- End with a thought-provoking question or call to action
- Include 3-5 relevant hashtags

Post length guidelines:
- For simple tips or insights: 2-4 short paragraphs
- For feature explanations or tutorials: 4-6 paragraphs with code
- Always prioritize clarity over length

Format code snippets using triple backticks with the language specified."""

        self.human_prompt = """Based on the following code context from a GitHub repository, write an engaging LinkedIn post.

Repository: {repo_url}

Recent Activity (Git Diff):
{git_diff}

Relevant Code Context:
{code_context}

Code Snippets to potentially include:
{code_snippets}

Guidelines:
1. Focus on what makes this code interesting or useful
2. If there's recent activity (git diff), highlight what's new
3. If no recent activity, find an interesting aspect of the existing code
4. Include a code snippet if it helps illustrate the point
5. Make it relatable to other developers
6. Post style: {post_style}

Write the LinkedIn post:"""

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(self.human_prompt)
        ])

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_post(
        self,
        repo_url: str,
        code_context: str,
        code_snippets: list[dict] = None,
        git_diff: str = "",
        post_style: str = "adaptive"
    ) -> str:
        """
        Generate a LinkedIn post from code context.

        Args:
            repo_url: GitHub repository URL
            code_context: Retrieved code context
            code_snippets: List of code snippet dicts with 'code', 'file', 'lines'
            git_diff: Recent git changes (optional)
            post_style: "short" for tips, "long" for tutorials, "adaptive" for auto

        Returns:
            Generated LinkedIn post
        """
        # Format code snippets
        snippets_text = ""
        if code_snippets:
            for i, snippet in enumerate(code_snippets[:3], 1):
                snippets_text += f"\n--- Snippet {i} from {snippet['file']} (lines {snippet['lines']}) ---\n"
                snippets_text += snippet['code']
                snippets_text += "\n"

        # Determine post style if adaptive
        if post_style == "adaptive":
            if git_diff and len(git_diff) > 200:
                post_style = "longer format highlighting the recent changes"
            elif len(code_context) > 2000:
                post_style = "longer format explaining the interesting patterns"
            else:
                post_style = "short and punchy tip or insight"

        result = self.chain.invoke({
            "repo_url": repo_url,
            "git_diff": git_diff or "No recent commits",
            "code_context": code_context,
            "code_snippets": snippets_text or "No specific snippets selected",
            "post_style": post_style
        })

        return result["text"].strip()

    def refine_post(self, post: str, feedback: str) -> str:
        """
        Refine a generated post based on feedback.

        Args:
            post: Original post
            feedback: User feedback for improvement

        Returns:
            Refined post
        """
        refine_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are helping refine a LinkedIn post. Make the requested changes while maintaining the engaging, authentic tone."
            ),
            HumanMessagePromptTemplate.from_template(
                "Original post:\n{post}\n\nFeedback: {feedback}\n\nRefined post:"
            )
        ])

        chain = LLMChain(llm=self.llm, prompt=refine_prompt)
        result = chain.invoke({"post": post, "feedback": feedback})

        return result["text"].strip()

    def generate_multiple_variations(
        self,
        repo_url: str,
        code_context: str,
        code_snippets: list[dict] = None,
        git_diff: str = "",
        num_variations: int = 3
    ) -> list[str]:
        """
        Generate multiple post variations for user selection.

        Args:
            repo_url: GitHub repository URL
            code_context: Retrieved code context
            code_snippets: List of code snippet dicts
            git_diff: Recent git changes
            num_variations: Number of variations to generate

        Returns:
            List of post variations
        """
        styles = ["short and punchy", "storytelling narrative", "tutorial/educational"]
        variations = []

        for i in range(min(num_variations, len(styles))):
            post = self.generate_post(
                repo_url=repo_url,
                code_context=code_context,
                code_snippets=code_snippets,
                git_diff=git_diff,
                post_style=styles[i]
            )
            variations.append(post)

        return variations
