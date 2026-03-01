import google.generativeai as genai
import time

class GeminiSummarizer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-pro-latest')

    def summarize(self, text: str) -> str:
        prompt = (
            "You are an expert corporate presenter. Read the following policy document and create a professional PowerPoint summary. "
            "For each key topic, generate a slide with:\n"
            "- A clear, concise slide title\n"
            "- 1-3 actionable bullet points\n"
            "- A short, relevant example for the topic (label as 'Example:')\n"
            "Format output as:\n"
            "Slide Title: <title>\n"
            "Bullets:\n"
            "- <bullet 1>\n"
            "- <bullet 2>\n"
            "Example: <short example text>\n"
            "Repeat for each key topic. Do not include any meta/instructional content.\n\nDocument:\n" + text
        )
        max_retries = 5
        wait_time = 70  # seconds
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    print(f"Quota error detected. Not retrying.")
                    raise RuntimeError("Gemini API quota error: Not retrying.")
                else:
                    raise
