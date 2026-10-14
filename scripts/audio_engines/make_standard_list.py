import os
import requests

def make_standard_list():
    trans_file = r"D:\Projects\ai-video-studio\models\reference_audio\slices_transcription.txt"
    out_list = r"D:\Projects\ai-video-studio\models\reference_audio\slicer_opt_standard.list"
    
    with open(trans_file, "r", encoding="utf-8") as fin, open(out_list, "w", encoding="utf-8") as fout:
        for line in fin:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                fname, text = parts
                fout.write(f"output/slicer_opt/{fname}|epanda_voice|zh|{text}\n")
                
    print(f"Generated {out_list}")
    
    # Upload to Colab
    url = "https://a6ff877b71b35e5521.gradio.live/upload"
    files = [('files', ('slicer_opt.list', open(out_list, 'rb'), 'text/plain'))]
    r = requests.post(url, files=files)
    print("Upload status:", r.status_code)
    print("Colab path:", r.text)

if __name__ == "__main__":
    make_standard_list()
