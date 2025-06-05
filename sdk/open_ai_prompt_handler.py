"""
open_ai_prompt_handler.py
This module provides functionality to interact with the OpenAI API
to generate summaries and analyze sentiment for articles.
"""

import logging

import openai

logger = logging.getLogger(__name__)
logger.info("Open AI Prompt started")


class OpenAIPrompt:
    """
    OpenAIPrompt class to interact with OpenAI API for generating article summaries.
    It uses the OpenAI API to create a short description of an article
    and analyze its sentiment.
    It formats the response in HTML for use in Telegram messages.
    """

    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key

    async def generate_summary(self, article_link):
        """
        Use OpenAI API to generate a short description for an article.
        Args:
            article_link (str): The link to the article to summarize.
        Returns:
            str: A formatted HTML summary of the article with sentiment analysis.
        """
        prompt = (
            f"Rezuma acest articol într-un scurt paragraf și analizează sentimentul"
            f"(Bullish, Bearish sau Neutral). Formatează răspunsul cu HTML "
            f"pentru Telegram(ex: <b> <i>):"
            f"\nLink: {article_link}"
        )

        return await self.get_response(prompt)

    async def get_response(self, prompt, model="gpt-4.1-mini", max_tokens=200):
        """
        Use OpenAI API to generate a short description for a prompt.
        Args:
            prompt (str): The prompt to send to the OpenAI API.
            model (str): The model to use for generating the response.
            max_tokens (int): The maximum number of tokens in the response.
        Returns:
            str: The generated summary or an error message if the request fails.
        """
        try:
            client = openai.OpenAI(
                api_key=self.openai_api_key
            )  # Use OpenAI's updated API client
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except (openai.OpenAIError, ValueError, TypeError) as e:
            print("Error generating summary: %s", e)
            logger.info("Error generating summary: %s", e)
            return "No summary available."
