import openai

from sdk.Logger import setup_logger
logger = setup_logger("log.log")
logger.info("Open AI Prompt started")

class OpenAIPrompt:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key

    async def generate_summary(self, article_link):
        """Use OpenAI API to generate a short description for an article."""
        prompt = (f"Rezuma acest articol într-un scurt paragraf și analizează sentimentul (Bullish, Bearish sau Neutral):"
                  f"\nLink: {article_link}")

        return await self.get_response(prompt)

    async def get_response(self, prompt, model='gpt-4o-mini'):
        """Use OpenAI API to generate a short description for a prompt."""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)  # Use OpenAI's updated API client
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            logger.info(f'Error generating summary: {e}')
            return "No summary available."