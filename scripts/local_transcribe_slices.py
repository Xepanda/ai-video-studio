import os
import glob
import time
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

def main():
    slices_dir = r"D:\Projects\ai-video-studio\models\reference_audio\slices"
    wav_files = sorted(glob.glob(os.path.join(slices_dir, "*.wav")))
    print(f"Found {len(wav_files)} slices to transcribe.")
    
    print("Loading SenseVoice model locally...")
    model = AutoModel(
        model="iic/SenseVoiceSmall",
        device="cpu",
        hub="ms",
        disable_update=True
    )
    
    list_entries = []
    t0 = time.time()
    for i, wav_path in enumerate(wav_files):
        res = model.generate(
            input=wav_path,
            language="zh",
            use_itn=True,
            batch_size_s=60
        )
        text = rich_transcription_postprocess(res[0]["text"]).strip()
        # Clean text
        text = text.replace(" ", "").replace("<|zh|>", "").replace("<|NEUTRAL|>", "").replace("<|Speech|>", "").replace("<|woitn|>", "")
        fname = os.path.basename(wav_path)
        print(f"[{i+1}/{len(wav_files)}] {fname} -> {text}")
        list_entries.append((fname, text))
        
    print(f"Transcription completed in {time.time() - t0:.2f}s!")
    
    out_list = r"D:\Projects\ai-video-studio\models\reference_audio\slices_transcription.txt"
    with open(out_list, "w", encoding="utf-8") as f:
        for fname, text in list_entries:
            f.write(f"{fname}\t{text}\n")
    print(f"Saved local transcription to {out_list}")

if __name__ == "__main__":
    main()
