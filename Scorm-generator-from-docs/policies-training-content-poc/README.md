# Agentic AI Policy Presenter - Usage Instructions

## Prerequisites
- Python 3.12+
- All dependencies installed (see `requirements.txt`)
- Policy documents placed in `policy_documents/` directory
- LibreOffice or PowerPoint for PPT to image conversion (manual step)

## Workflow Steps
1. **Fetch Documents**
   - Place your policy documents in the `policy_documents/` folder.
2. **Summarize Documents**
   - The main script uses Gemini API to summarize the first document found.
   - Set your Gemini API key as an environment variable `GEMINI_API_KEY`.
3. **Generate PPT**
   - The summary is converted into a PowerPoint presentation (`output.pptx`).
4. **Convert PPT to Images**
   - Use LibreOffice or PowerPoint to export slides as images (e.g., `slide_1.png`, `slide_2.png`, ...).
   - Place images in the `ppt_images/` directory.
   - Example LibreOffice command:
     ```
     libreoffice --headless --convert-to png output.pptx --outdir ppt_images/
     ```
5. **Generate Audio**
   - The summary is converted to audio (`output.mp3`) using TTS.
6. **Generate Video**
   - Images and audio are combined into a video (`output.mp4`) using ffmpeg-python.

## Running the Workflow
Activate your virtual environment and run:
```
python src/main.py
```

## Troubleshooting
- Ensure all dependencies are installed:
  ```
  pip install -r requirements.txt
  ```
- If you encounter import errors, verify your Python environment and kernel selection.
- For video generation, ensure images are named sequentially (`slide_1.png`, `slide_2.png`, ...).

## Customization
- You can modify `src/main.py` to process multiple documents or change output formats.
- Adjust TTS settings in `audio/audio_generator.py` for different voices or languages.

## Contact
For issues or feature requests, open an issue in the repository.
