import openai
import logging

from datetime import datetime

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

class OpenAIPrompt:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key

    async def generate_summary(self, article_link):
        """Use OpenAI API to generate a short description for an article."""
        prompt = f"Rezuma articolul într-un scurt paragraf:\nLink: {article_link}"

        return await self.get_response(prompt)

    async def get_response(self, prompt):
        """Use OpenAI API to generate a short description for a prompt."""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)  # Use OpenAI's updated API client
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            logging.info(f'Error generating summary: {e}')
            return "No summary available."