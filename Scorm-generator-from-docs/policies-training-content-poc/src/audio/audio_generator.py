import pyttsx3
from gtts import gTTS
import time
from pydub import AudioSegment

class AudioGenerator:
    def __init__(self, method='gtts', voice=None, rate=180, volume=1.0):
        """
        method: 'gtts' or 'pyttsx3'
        voice: voice id or name (pyttsx3 only)
        rate: speech rate (words per minute)
        volume: float between 0.0 and 1.0
        """
        self.method = method
        self.voice = voice
        self.rate = rate
        self.volume = volume

    def _fix_split_words(self, text):
        # Attempt to fix words split at line breaks (e.g., 'Boundarie\ns') and at the end of lines
        import re
        # Remove hyphenation at line breaks (e.g., 'Boundarie-\ns' -> 'Boundaries')
        text = re.sub(r'(\w+)-[\n\r]+(\w+)', r'\1\2', text)
        # Remove line breaks within words (e.g., 'Boundarie\ns' -> 'Boundaries')
        text = re.sub(r'(\w+)[\n\r]+(\w+)', r'\1\2', text)
        return text

    def generate_audio(self, text: str, output_path: str):
        import re
        # Split summary into sentences, filter out empty/invalid lines
        lines = [line.strip() for line in re.split(r'[\n\r]+', text) if line.strip()]
        # Remove lines that are just 'w', 'ww', etc. or contain 'Slide X' or mention 'slide' at all
        lines = [line for line in lines if not re.fullmatch(r'w+', line, re.IGNORECASE)]
        lines = [line for line in lines if not re.search(r'\bslide\b', line, re.IGNORECASE)]
        # Join lines for natural speech
        speech_text = ' '.join(lines)
        sanitized_text = re.sub(r'[^\w\s.,;:!\?\-\'\"]+', '', speech_text)
        if not sanitized_text:
            print(f"Skipping audio generation for empty text: {output_path}")
            return
        if self.method == 'gtts':
            tts = gTTS(sanitized_text)
            tts.save(output_path)
        elif self.method == 'pyttsx3':
            engine = pyttsx3.init()
            if self.voice:
                voices = engine.getProperty('voices')
                for v in voices:
                    if self.voice.lower() in v.name.lower() or self.voice == v.id:
                        engine.setProperty('voice', v.id)
                        break
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            engine.save_to_file(sanitized_text, output_path)
            engine.runAndWait()
        else:
            raise ValueError('Unsupported TTS method')

    def generate_slide_audio(self, slide_text: str, heading: str = None, output_path: str = None, pause_duration: float = 0.5):
        """
        Generate audio for a slide, reading the heading first, then a pause, then the bullet points.
        For 'gtts', combine heading and bullet text into one string, add a period and ellipsis for pause.
        """
        import re
        if self.method == 'gtts':
            # Combine heading and bullet text with a pause marker
            heading_fixed = self._fix_split_words(heading) if heading else ""
            slide_text_fixed = self._fix_split_words(slide_text) if slide_text else ""
            # Use a period and ellipsis to simulate a pause in TTS
            combined_text = f"{heading_fixed}. ... {slide_text_fixed}" if heading_fixed else slide_text_fixed
            sanitized_text = re.sub(r'[^\u0000-\u007F]+', '', combined_text)
            if not sanitized_text.strip():
                print(f"Skipping audio generation for empty text: {output_path}")
                return
            tts = gTTS(sanitized_text)
            tts.save(output_path)
        else:
            import pyttsx3
            from pydub import AudioSegment
            engine = pyttsx3.init()
            audio_segments = []
            if heading and heading.strip():
                heading_fixed = self._fix_split_words(heading)
                engine.save_to_file(heading_fixed, 'heading_tmp.mp3')
                engine.runAndWait()
                audio_segments.append(AudioSegment.from_file('heading_tmp.mp3'))
                audio_segments.append(AudioSegment.silent(duration=int(pause_duration*1000)))
            if slide_text and slide_text.strip():
                slide_text_fixed = self._fix_split_words(slide_text)
                engine.save_to_file(slide_text_fixed, 'slide_tmp.mp3')
                engine.runAndWait()
                audio_segments.append(AudioSegment.from_file('slide_tmp.mp3'))
            if audio_segments:
                final_audio = sum(audio_segments)
                if output_path:
                    final_audio.export(output_path, format='mp3')
            # Clean up temp files
            import os
            for f in ['heading_tmp.mp3', 'slide_tmp.mp3']:
                if os.path.exists(f):
                    os.remove(f)
