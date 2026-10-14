import os
import glob
import json
import time
import requests

def upload_all_dataset():
    slices_dir = r"D:\Projects\ai-video-studio\models\reference_audio\slices"
    trans_file = r"D:\Projects\ai-video-studio\models\reference_audio\slices_transcription.txt"
    upload_url = "https://a6ff877b71b35e5521.gradio.live/upload"
    
    # Load transcriptions
    trans_dict = {}
    with open(trans_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                trans_dict[parts[0]] = parts[1]
                
    wav_files = sorted(glob.glob(os.path.join(slices_dir, "*.wav")))
    print(f"Total slices to upload: {len(wav_files)}")
    
    colab_paths = {}
    t0 = time.time()
    # Upload in batches of 10 files
    batch_size = 10
    for i in range(0, len(wav_files), batch_size):
        batch = wav_files[i:i+batch_size]
        files = [('files', (os.path.basename(p), open(p, 'rb'), 'audio/wav')) for p in batch]
        print(f"Uploading batch {i//batch_size + 1}/{(len(wav_files)+batch_size-1)//batch_size} ({len(batch)} files)...")
        r = requests.post(upload_url, files=files, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Upload failed: {r.status_code} {r.text}")
        uploaded = r.json()
        for local_p, remote_p in zip(batch, uploaded):
            fname = os.path.basename(local_p)
            colab_paths[fname] = remote_p
            
    print(f"Successfully uploaded {len(colab_paths)} wav files in {time.time() - t0:.2f}s!")
    
    # Generate local list file
    local_list = r"D:\Projects\ai-video-studio\models\reference_audio\epanda_voice.list"
    with open(local_list, "w", encoding="utf-8") as f:
        for fname in sorted(colab_paths.keys()):
            remote_path = colab_paths[fname]
            text = trans_dict.get(fname, "")
            if text:
                f.write(f"{remote_path}|epanda_voice|zh|{text}\n")
                
    print(f"Generated {local_list} with {len(colab_paths)} entries.")
    
    # Upload the .list file itself to Colab
    print("Uploading .list file to Colab...")
    files = [('files', ('epanda_voice.list', open(local_list, 'rb'), 'text/plain'))]
    r = requests.post(upload_url, files=files, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"List upload failed: {r.status_code} {r.text}")
    remote_list_path = r.json()[0]
    print(f"Remote .list path on Colab: {remote_list_path}")
    
    # Save mapping info
    info = {
        "remote_list_path": remote_list_path,
        "count": len(colab_paths),
        "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(r"D:\Projects\ai-video-studio\models\reference_audio\upload_manifest.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
        
    return remote_list_path

if __name__ == "__main__":
    path = upload_all_dataset()
    print("SUCCESS! Remote list path is:", path)
