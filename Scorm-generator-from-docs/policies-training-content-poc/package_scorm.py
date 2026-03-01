import zipfile
import os
import glob
import subprocess
def generate_scorm_video_html(video_files, video_titles=None):
    html_files = []
    if video_titles is None:
        video_titles = [f"Policy Training Video Part {i+1}" for i in range(len(video_files))]
    for idx, file in enumerate(video_files):
        title = video_titles[idx] if idx < len(video_titles) else f"Policy Training Video Part {idx+1}"
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f8f8; }}
        .video-container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; max-width: 800px; margin: auto; }}
        h1 {{ text-align: center; }}
        video {{ width: 100%; border-radius: 8px; margin-bottom: 20px; }}
        .desc {{ font-size: 18px; color: #333; text-align: center; margin-bottom: 20px; }}
        .part-label {{ text-align:center; font-weight:bold; margin-bottom:8px; }}
    </style>
</head>
<body>
    <div class="video-container">
        <h1>{title}</h1>
        <video controls><source src='{file}' type='video/mp4'>Your browser does not support the video tag.</video>
        <div class="desc">
            This video summarizes the key points of the policy document with audio narration and slide visuals.
        </div>
    </div>
</body>
</html>
'''
        html_filename = f"scorm_video_part{idx+1}.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html)
        html_files.append(html_filename)
    return html_files

def update_manifest(video_files, html_files, course_name='Policy Overview'):
    # Read the original manifest
    with open("imsmanifest.xml", "r", encoding="utf-8") as f:
        manifest = f.read()
    from xml.etree import ElementTree as ET
    # Register namespaces for parsing and writing
    ET.register_namespace('adlcp', 'http://www.adlnet.org/xsd/adlcp_rootv1p2')
    ET.register_namespace('', 'http://www.imsproject.org/xsd/imscp_rootv1p1p2')
    tree = ET.ElementTree(ET.fromstring(manifest))
    org = tree.find(".//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}organization")
    resources = tree.find(".//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resources")
    # Remove old video items/resources
    for item in list(org):
        if item.tag.endswith('item') and item.attrib.get('identifierref', '').startswith('res_video'):
            org.remove(item)
    for res in list(resources):
        if res.attrib.get('identifier', '').startswith('res_video'):
            resources.remove(res)
    # Add/replace course-level title
    found_title = False
    for child in org:
        if child.tag.endswith('title'):
            child.text = course_name
            found_title = True
            break
    if not found_title:
        title_elem = ET.Element('title')
        title_elem.text = course_name
        org.insert(0, title_elem)
    # Add new items/resources
    adlcp_ns = '{http://www.adlnet.org/xsd/adlcp_rootv1p2}'
    # Use video_titles for dynamic titles
    video_titles = globals().get('video_titles', [f'Policy Training Video Part {i+1}' for i in range(len(video_files))])
    for idx, (file, html) in enumerate(zip(video_files, html_files)):
        item = ET.Element('item', identifier=f'item_video_{idx+1}', identifierref=f'res_video_{idx+1}')
        title = ET.Element('title')
        title.text = video_titles[idx] if idx < len(video_titles) else f'Policy Training Video Part {idx+1}'
        item.append(title)
        org.insert(idx, item)
        res = ET.Element('resource', identifier=f'res_video_{idx+1}', type='webcontent', href=html)
        res.set(adlcp_ns + 'scormType', 'asset')
        file_elem = ET.Element('file', href=html)
        res.append(file_elem)
        file_elem2 = ET.Element('file', href=file)
        res.append(file_elem2)
        resources.append(res)
    # Update PPT resource in manifest to use ppt_dst
    ppt_dst = f'{course_name}.pptx'
    resources = tree.find(".//{http://www.imsproject.org/xsd/imscp_rootv1p1p2}resources")
    for res in list(resources):
        if res.attrib.get('identifier', '') == 'ppt_resource':
            res.set('href', ppt_dst)
            for file_elem in res.findall("{http://www.imsproject.org/xsd/imscp_rootv1p1p2}file"):
                file_elem.set('href', ppt_dst)
    ET.indent(tree, space="  ", level=0)
    tree.write("imsmanifest.xml", encoding="utf-8", xml_declaration=True)


def merge_videos_ffmpeg(video_files, output_file):
    # Merge multiple video files into one using ffmpeg
    with open("video_parts.txt", "w") as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "video_parts.txt", "-c", "copy", output_file
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error merging videos: {e}")
    finally:
        os.remove("video_parts.txt")

def mix_audio_with_video_ffmpeg(video_file, audio_file, output_file):
    # Mix background audio into video using ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", video_file, "-i", audio_file,
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", output_file
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error mixing audio: {e}")

def package_scorm():
    # Find all video parts
    video_files = sorted(glob.glob("output_part*.mp4"))
    # Try to load video_titles from a file if present
    video_titles = None
    if os.path.exists('video_titles.txt'):
        with open('video_titles.txt', 'r', encoding='utf-8') as f:
            # Only keep non-empty, non-blank titles
            video_titles = [line.strip() for line in f.readlines() if line.strip() and line.strip().lower() != 'no title']
    # Dynamically set course name from policy document filename
    policy_doc_dir = os.path.join(os.path.dirname(__file__), 'policy_documents')
    policy_docs = [f for f in os.listdir(policy_doc_dir) if f.lower().endswith('.pdf')]
    course_name = os.path.splitext(policy_docs[0])[0] if policy_docs else 'Policy Overview'
    ppt_src = 'output.pptx'
    ppt_dst = f'{course_name}.pptx'
    # Always use the dynamically named PPT for packaging
    if os.path.exists(ppt_src):
        # Rename PPT for packaging (do not overwrite if already correct)
        if ppt_src != ppt_dst:
            import shutil
            shutil.copyfile(ppt_src, ppt_dst)
    # ...existing code...
    if video_files:
        html_files = generate_scorm_video_html(video_files, video_titles=video_titles)
        # Set global for manifest
        globals()['video_titles'] = video_titles
        update_manifest(video_files, html_files, course_name=course_name)
        scorm_files = [
            "imsmanifest.xml",
            "scorm_quiz.html",
            "quiz_output.json",
            ppt_dst
        ] + video_files + html_files
        # Optionally merge all parts into output.mp4 for reference only
        merge_videos_ffmpeg(video_files, "output.mp4")
        if os.path.exists("output.mp4") and "output.mp4" not in scorm_files:
            scorm_files.append("output.mp4")
    elif os.path.exists("output.mp4"):
        # Only one video, use output.mp4 (music already mixed)
        html_files = generate_scorm_video_html(["output.mp4"])
        update_manifest(["output.mp4"], html_files, course_name=course_name)
        scorm_files = [
            "imsmanifest.xml",
            "scorm_quiz.html",
            "quiz_output.json",
            ppt_dst,
            "output.mp4"
        ] + html_files
    else:
        scorm_files = ["imsmanifest.xml", "scorm_quiz.html", "quiz_output.json", ppt_dst]
    with zipfile.ZipFile(OUTPUT_ZIP, "w") as zf:
        for fname in scorm_files:
            if os.path.exists(fname):
                zf.write(fname)
            else:
                print(f"Warning: {fname} not found.")
    print(f"SCORM package created: {OUTPUT_ZIP}")

OUTPUT_ZIP = "policy_training_scorm.zip"

if __name__ == "__main__":
    package_scorm()
