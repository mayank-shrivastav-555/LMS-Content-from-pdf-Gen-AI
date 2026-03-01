
from audio.audio_generator import AudioGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
from typing import List, Dict, Optional

def read_document(file_path: str) -> str:
    import PyPDF2
    if file_path.lower().endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def parse_slides_with_examples(summary_text: str) -> List[Dict]:
    slides = []
    current = {}
    for line in summary_text.split('\n'):
        line = line.strip()
        if line.startswith('Slide Title:'):
            if current:
                slides.append(current)
                current = {}
            current['title'] = line.replace('Slide Title:', '').strip()
            current['bullets'] = []
        elif line.startswith('- '):
            if 'bullets' not in current:
                current['bullets'] = []
            current['bullets'].append(line[2:].strip())
        elif line.startswith('Example:'):
            current['example'] = line.replace('Example:', '').strip()
    if current:
        slides.append(current)
    return slides

def generate_ppt(slides: List[Dict], ppt_output: str, background_image: Optional[str], doc_filename: str,intro_image: Optional[str] ) -> List[List[str]]:
    ppt = PPTCreator(background_image_path=background_image)
    # Adding the SI-BONE intro image, as the first slide
    if intro_image and os.path.exists(intro_image):
        ppt.add_intro_image_slide(intro_image)
    ppt.add_title_slide('Policy Summary', os.path.basename(doc_filename))
    slide_chunks = []
    for slide in slides:
        ppt.add_bullet_slide(slide['bullets'], title=slide['title'])
        slide_chunks.append(slide['bullets'])
        example_heading = f"Example: {slide['title']}" if slide.get('title') else "Example"
        ppt.add_bullet_slide([slide.get('example', '')], title=example_heading)
        slide_chunks.append([slide.get('example', '')])
    # Add Thank You slide at the end
    ppt.add_thankyou_slide()
    slide_chunks.append(["Thank You!"])
    ppt.save(ppt_output)
    return slide_chunks
# def generate_audio_files(slide_chunks: List[List[str]], slides: List[Dict], images_dir: str, audio_gen: AudioGenerator) -> List[str]:
#     slide_audio_files = []
#     for idx, chunk in enumerate(slide_chunks):
#         chunk_text = ' '.join(chunk)
#         heading = None
#         if idx < len(slides)*2:
#             slide_obj = slides[idx//2] if idx//2 < len(slides) else None
#             if slide_obj:
#                 if idx % 2 == 0:
#                     heading = slide_obj.get('title', None)
#                 else:
#                     heading = f"Example: {slide_obj.get('title', '')}" if slide_obj.get('title') else "Example"
#         audio_path = os.path.join(images_dir, f'slide_{idx+1}.mp3')
#         if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
#             print(f"[CACHE] Skipping audio generation for slide {idx+1}: {audio_path} exists.")
#         else:
#             print(f"Generating audio for slide {idx+1}: heading='{heading}'")
#             audio_gen.generate_slide_audio(chunk_text, heading=heading, output_path=audio_path)
#         slide_audio_files.append(audio_path)
#     return slide_audio_files

def cleanup_generated_files(images_dir: str):
    import glob
    print('Cleaning up generated audio and image files...')
    for audio_file in glob.glob(os.path.join(images_dir, 'slide_*.mp3')):
        try:
            os.remove(audio_file)
            print(f"Deleted {audio_file}")
        except Exception as e:
            print(f"Error deleting {audio_file}: {e}")
    for img_file in glob.glob(os.path.join(images_dir, '*.png')):
        if 'icon' not in img_file:
            try:
                os.remove(img_file)
                print(f"Deleted {img_file}")
            except Exception as e:
                print(f"Error deleting {img_file}: {e}")

import os
from fetchers.document_fetcher import DocumentFetcher
from summarizers.summary_generator import GeminiSummarizer
from ppt.ppt_creator import PPTCreator
from audio.audio_generator import AudioGenerator
from video.video_generator import VideoGenerator
from quiz.quiz_generator import QuizGenerator
import PyPDF2
import google.generativeai as genai

# Set your Gemini API key here or via environment variable
# GEMINI_API_KEY = "AIzaSyBxM3eBsqZshdRv_500LQ3lKonVRXoHJ-w"
# GEMINI_API_KEY = "AIzaSyDmP4oegquGsALx7WA4Xyke8ibOH0OtMn8"
GEMINI_API_KEY = "AIzaSyCBYLPtuYCQxGd7TCHNzMP4Yw8kvYKjkgs"
# Paths
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'policy_documents')
DOCUMENTS_DIR = os.path.abspath(DOCUMENTS_DIR)  # Directory containing policy docs
PPT_OUTPUT = 'output.pptx'
AUDIO_OUTPUT = 'output.mp3'
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'ppt_images')
IMAGES_DIR = os.path.abspath(IMAGES_DIR)  # Directory for PPT slide images
VIDEO_OUTPUT = 'output.mp4'
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Toggle for static background
USE_STATIC_BG = True  # Set to True for static, False for fetch
import glob
# Find static background in src/utils/default/ with supported extensions
STATIC_BG_DIR = os.path.join(os.path.dirname(__file__), 'utils', 'default')
STATIC_BG_PATH = None
for ext in ['.jpg', '.jpeg', '.png', '.svg']:
    candidate = os.path.join(STATIC_BG_DIR, f'background{ext}')
    if os.path.exists(candidate):
        STATIC_BG_PATH = candidate
        break
if not STATIC_BG_PATH:
    print('Warning: No static background image found in src/utils/default/.')
    
INTRO_IMG_PATH = None
for ext in ['.jpg', '.jpeg', '.png', '.svg']:
    candidate = os.path.join(STATIC_BG_DIR, f'SI-BONE-intro{ext}')
    if os.path.exists(candidate):
        INTRO_IMG_PATH = candidate
        break
if not INTRO_IMG_PATH:
    print('Warning: No static background image found in src/utils/default/.')
    
# genai.configure(api_key=GEMINI_API_KEY)
# models = list(genai.list_models())
# print("models =====================> :", models)

# Example mode toggle: 'separate-slide' or 'sub-bullet'
example_mode = 'separate-slide'  # Change to 'sub-bullet' for sub-bullet examples

# --- Modular Workflow ---
def main():
    try:
        fetcher = DocumentFetcher(DOCUMENTS_DIR)
        doc_files = fetcher.fetch_documents()
        if not doc_files:
            logging.error('No documents found.')
            return
        doc_text = read_document(doc_files[0])
        summarizer = GeminiSummarizer(GEMINI_API_KEY)
        summary = summarizer.summarize(doc_text)
        summary_points = summary.split('\n')
        slides = parse_slides_with_examples(summary)
        slide_chunks = generate_ppt(slides, PPT_OUTPUT, STATIC_BG_PATH if USE_STATIC_BG else None, doc_files[0], INTRO_IMG_PATH)
        audio_gen = AudioGenerator(method='gtts', rate=170, volume=0.9)
        # Generate audio: only for slides 1..N-2 (skip 0th and last)
        slide_audio_files = []
        from pydub import AudioSegment
        background_music_path = os.path.join(os.path.dirname(__file__), 'utils', 'default', 'background.mp3')
        # First slide (title) - only background music
        first_slide_audio_path = os.path.join(IMAGES_DIR, 'slide_0_bg_only.mp3')
        silence = AudioSegment.silent(duration=3000)
        if os.path.exists(background_music_path):
            bg_music = AudioSegment.from_file(background_music_path)
            bg_music = bg_music - 18
            bg_music = bg_music[:len(silence)] if len(bg_music) > len(silence) else bg_music
            mixed = silence.overlay(bg_music)
            mixed.export(first_slide_audio_path, format='mp3')
        else:
            silence.export(first_slide_audio_path, format='mp3')
        # added2 copies of first slide audio for 2 intro slides
        slide_audio_files.append(first_slide_audio_path)
        slide_audio_files.append(first_slide_audio_path)

        # Slides 1..N-2 (TTS)
        # Generate audio for each content slide and pair with correct image
        for idx in range(0, len(slide_chunks)-1):
            chunk = slide_chunks[idx]
            chunk_text = ' '.join(chunk)
            heading = None
            if idx < len(slides) * 2:
                slide_obj = slides[idx // 2]
                if idx % 2 == 0:
                    heading = slide_obj.get('title', None)
                else:
                    heading = f"Example: {slide_obj.get('title', '')}" if slide_obj.get('title') else "Example"
            audio_path = os.path.join(IMAGES_DIR, f'slide_{idx}.mp3')
            try:
                audio_gen.generate_slide_audio(chunk_text, heading=heading, output_path=audio_path)
                # Check if file was actually created and is valid
                if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
                    logging.error(f"TTS API returned 200 but no valid audio for slide {idx}: {audio_path}. Check API response and payload.")
                else:
                    slide_audio_files.append(audio_path)
            except Exception as e:
                logging.error(f"Error generating audio for slide {idx}: {e}")

        # Thank You slide (last) - only background music
        thankyou_audio_path = os.path.join(IMAGES_DIR, 'slide_thankyou_bg_only.mp3')
        silence_thankyou = AudioSegment.silent(duration=3000)
        if os.path.exists(background_music_path):
            bg_music_thankyou = AudioSegment.from_file(background_music_path)
            bg_music_thankyou = bg_music_thankyou - 18
            bg_music_thankyou = bg_music_thankyou[:len(silence_thankyou)] if len(bg_music_thankyou) > len(silence_thankyou) else bg_music_thankyou
            mixed_thankyou = silence_thankyou.overlay(bg_music_thankyou)
            mixed_thankyou.export(thankyou_audio_path, format='mp3')
        else:
            silence_thankyou.export(thankyou_audio_path, format='mp3')
        slide_audio_files.append(thankyou_audio_path)

        video_gen = VideoGenerator()
        genai_model = summarizer.model
        icon_dir = os.path.join(IMAGES_DIR, 'icons')
        icon_paths = [os.path.join(icon_dir, f) for f in os.listdir(icon_dir) if f.endswith('.png')] if os.path.exists(icon_dir) else None
        image_files = video_gen.ppt_to_images(PPT_OUTPUT, IMAGES_DIR, gemini_model=genai_model, icon_paths=icon_paths, default_img_path=STATIC_BG_PATH, use_image_background=USE_STATIC_BG,intro_img_path=INTRO_IMG_PATH)
        overlay_texts = ["Intro"] + [" ".join(chunk[:2]) if chunk else "" for chunk in slide_chunks[1:-1]] + ["Thank You"]

        def get_audio_duration(audio_path: str) -> float:
            audio = AudioSegment.from_file(audio_path)
            return audio.duration_seconds
        slide_durations = [get_audio_duration(a) for a in slide_audio_files]

        # --- Updated batching logic: intro, odd (content), even (example), thank you ---
        video_parts = []
        video_parts = []
        video_titles = []
        intro_img_idx = 0
        thankyou_img_idx = len(image_files) - 1
        intro_audio_idx = 0
        thankyou_audio_idx = len(slide_audio_files) - 1
        # Start from slide_1.png (content), slide_2.png (example), etc.
        # --- New batching logic: iterate over slides, always include intro and thank you ---
        logging.info(f"image_files: {image_files},{len(image_files)},\n slide_audio_files:{slide_audio_files}, {len(slide_audio_files)},\n overlay_texts: {len(overlay_texts)}, slides: {len(slides)}")
        # exit(0)
        for slide_idx, slide in enumerate(slides):
            part_images = []
            part_audios = []
            part_overlay = []

            # --- Always include BOTH intro slides ---
            for i in range(2):  # 0 and 1
                if i < len(image_files):
                    part_images.append(image_files[i])
                if i < len(slide_audio_files):
                    part_audios.append(slide_audio_files[i])
                if i < len(overlay_texts):
                    part_overlay.append(overlay_texts[i])

            # --- Content slide ---
            content_img_idx = 2 + slide_idx * 2
            content_audio_idx = 2 + slide_idx * 2
            if content_img_idx < len(image_files):
                part_images.append(image_files[content_img_idx])
            if content_audio_idx < len(slide_audio_files):
                part_audios.append(slide_audio_files[content_audio_idx])
            if content_img_idx < len(overlay_texts):
                part_overlay.append(overlay_texts[content_img_idx])

            # --- Example slide ---
            example_img_idx = content_img_idx + 1
            example_audio_idx = content_audio_idx + 1
            if example_img_idx < len(image_files):
                part_images.append(image_files[example_img_idx])
            if example_audio_idx < len(slide_audio_files):
                part_audios.append(slide_audio_files[example_audio_idx])
            if example_img_idx < len(overlay_texts):
                part_overlay.append(overlay_texts[example_img_idx])

            # --- Always add thank you ---
            if thankyou_img_idx < len(image_files):
                part_images.append(image_files[thankyou_img_idx])
            if thankyou_audio_idx < len(slide_audio_files):
                part_audios.append(slide_audio_files[thankyou_audio_idx])
            if thankyou_img_idx < len(overlay_texts):
                part_overlay.append(overlay_texts[thankyou_img_idx])

            # --- Only add if valid content ---
            if len(part_images) > 3 and len(part_audios) > 3:  # at least intros + 1 content
                part_output = f"output_part{slide_idx+1}.mp4"
                video_parts.append((part_images, part_audios, part_overlay, part_output))
                video_titles.append(slide.get('title', f'Video {slide_idx+1}'))
            else:
                logging.warning(f"Skipping video part {slide_idx+1}: not enough images/audios for content slide.")
        if not video_parts:
            logging.critical("No video parts generated. Check slide and audio extraction.")
            return
        # Save video_titles.txt for SCORM packaging
        with open('video_titles.txt', 'w', encoding='utf-8') as vt:
            for title in video_titles:
                vt.write(title + '\n')
        # Generate videos
        for part_idx, (part_images, part_audios, part_overlay_texts, part_output) in enumerate(video_parts):
            try:
                video_gen.create_video(
                    part_images,
                    part_audios,
                    part_output,
                    overlay_texts=part_overlay_texts,
                    background_music_path=background_music_path,
                    slide_pause_duration=1
                )
            except Exception as e:
                logging.error(f"Error generating video part {part_idx+1}: {e}")
        # Quiz generation temporarily disabled to save Gemini API calls
        try:
            quiz = QuizGenerator(summary_points, num_questions=5, api_key=GEMINI_API_KEY)
            quiz.export_quiz("quiz_output.txt")
            quiz.export_quiz_json("quiz_output.json")
        except Exception as e:
            logging.error(f"Error generating quiz: {e}")
        logging.info(f'Workflow complete! Video saved as {VIDEO_OUTPUT}')
        import subprocess
        scorm_packager = os.path.join(os.path.dirname(__file__), '..', 'package_scorm.py')
        if os.path.exists(scorm_packager):
            logging.info('Packaging SCORM output...')
            try:
                result = subprocess.run(['python', scorm_packager], capture_output=True, text=True)
                logging.info(result.stdout)
                if result.stderr:
                    logging.error(f'SCORM packaging errors: {result.stderr}')
            except Exception as e:
                logging.error(f'Error running SCORM packaging: {e}')
        else:
            logging.warning(f'SCORM packaging script not found: {scorm_packager}')
        cleanup_generated_files(IMAGES_DIR)
    except Exception as e:
        logging.critical(f'Fatal error in workflow: {e}')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f'Fatal error in workflow: {e}')
        # Cleanup ppt_images directory on any fatal error
        import glob, os
        images_dir = os.path.join(os.path.dirname(__file__), '..', 'ppt_images')
        for audio_file in glob.glob(os.path.join(images_dir, 'slide_*.mp3')):
            try:
                os.remove(audio_file)
                logging.info(f"Deleted {audio_file}")
            except Exception as del_e:
                logging.error(f"Error deleting {audio_file}: {del_e}")
        for img_file in glob.glob(os.path.join(images_dir, '*.png')):
            if 'icon' not in img_file:
                try:
                    os.remove(img_file)
                    logging.info(f"Deleted {img_file}")
                except Exception as del_e:
                    logging.error(f"Error deleting {img_file}: {del_e}")