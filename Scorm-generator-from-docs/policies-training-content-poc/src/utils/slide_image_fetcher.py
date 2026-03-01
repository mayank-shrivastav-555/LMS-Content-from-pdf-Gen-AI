import requests
import os

UNSPLASH_ACCESS_KEY = "LZ5NQLfb8Leo3z30mskp057Ti5KK0yrWJU-ievAClLA"
UNSPLASH_SECRET_KEY = "sUV4kTB8CNfCXzU2yfih8wYjbfxQ-4S-7LY7kcLyziE"
PIXABAY_API_KEY = "52710038-cc45f466468634a5893322b54"

class SlideImageFetcher:
    def __init__(self, unsplash_key=None, pixabay_key=None):
        self.unsplash_key = unsplash_key or UNSPLASH_ACCESS_KEY
        self.pixabay_key = pixabay_key or PIXABAY_API_KEY

    def fetch_unsplash(self, query):
        url = f"https://api.unsplash.com/photos/random?query={query}&client_id={self.unsplash_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                img_url = data.get("urls", {}).get("regular")
                if img_url:
                    print(f"Image fetched from Unsplash for query: '{query}'")
                return img_url
        except Exception as e:
            print(f"Unsplash error for query '{query}': {e}")
        return None

    def fetch_pixabay(self, query):
        url = f"https://pixabay.com/api/?key={self.pixabay_key}&q={query}&image_type=photo&per_page=3"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", [])
                if hits:
                    img_url = hits[0].get("webformatURL")
                    if img_url:
                        print(f"Image fetched from Pixabay for query: '{query}'")
                    return img_url
        except Exception as e:
            print(f"Pixabay error for query '{query}': {e}")
        return None

    def fetch_gemini(self, prompt, gemini_model):
        # Fallback: Use Gemini to suggest an image prompt or URL
        try:
            response = gemini_model.generate_content(f"Suggest a relevant image URL or prompt for: {prompt}")
            import re
            urls = re.findall(r'(https?://\S+)', response.text)
            if urls:
                print(f"Image URL suggested by Gemini for prompt: '{prompt}'")
                return urls[0]
            print(f"Gemini prompt fallback used for: '{prompt}'")
            return response.text.strip()
        except Exception as e:
            print(f"Gemini fallback error for prompt '{prompt}': {e}")
        return None

    def clean_query(self, text):
        # Remove stopwords and generic terms, limit to 5 keywords
        import re
        stopwords = set(["slide", "summary", "policy", "presentation", "overview", "the", "and", "of", "for", "in", "to"])
        words = re.findall(r'\w+', text.lower())
        keywords = [w for w in words if w not in stopwords]
        return ' '.join(keywords[:5]) if keywords else 'policy training'

    def fetch_image(self, query, gemini_model=None):
        clean_q = self.clean_query(query)
        # Try Unsplash first
        img_url = self.fetch_unsplash(clean_q)
        if img_url:
            return img_url
        # Try Pixabay next
        img_url = self.fetch_pixabay(clean_q)
        if img_url:
            return img_url
        # Fallback to Gemini prompt
        if gemini_model:
            img_url = self.fetch_gemini(clean_q, gemini_model)
            if img_url:
                return img_url
        print(f"No image found for query: '{clean_q}'. Using default placeholder.")
        # Optionally, return a local placeholder image path
        return None
