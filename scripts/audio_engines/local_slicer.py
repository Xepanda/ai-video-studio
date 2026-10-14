import os
import sys
import wave
import numpy as np

def slice_audio_local(wav_path, out_dir, min_sec=3.0, max_sec=10.0, silence_thresh=0.01):
    os.makedirs(out_dir, exist_ok=True)
    with wave.open(wav_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)
        
    dtype = np.int16 if sampwidth == 2 else np.int32
    audio = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
        
    max_val = np.max(np.abs(audio)) + 1e-6
    norm_audio = audio / max_val
    
    # Calculate energy in 100ms frames
    frame_size = int(framerate * 0.1) # 100ms
    n_chunks = len(norm_audio) // frame_size
    energies = [np.mean(np.abs(norm_audio[i*frame_size:(i+1)*frame_size])) for i in range(n_chunks)]
    
    # Simple silence-based split
    split_points = [0]
    min_frames = int(min_sec / 0.1)
    max_frames = int(max_sec / 0.1)
    
    last_split = 0
    for i in range(min_frames, n_chunks):
        cur_len = i - last_split
        if cur_len >= max_frames:
            split_points.append(i * frame_size)
            last_split = i
        elif cur_len >= min_frames and energies[i] < silence_thresh:
            split_points.append(i * frame_size)
            last_split = i
            
    if split_points[-1] < len(audio):
        split_points.append(len(audio))
        
    segments = []
    for idx in range(len(split_points) - 1):
        start = split_points[idx]
        end = split_points[idx+1]
        seg_audio = audio[start:end].astype(dtype)
        seg_name = f"my_voice_slice_{idx:03d}.wav"
        seg_path = os.path.join(out_dir, seg_name)
        
        with wave.open(seg_path, 'wb') as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(sampwidth)
            out_wf.setframerate(framerate)
            out_wf.writeframes(seg_audio.tobytes())
            
        dur = len(seg_audio) / framerate
        segments.append((seg_path, dur))
        
    print(f"Successfully sliced into {len(segments)} segments in {out_dir}")
    return segments

if __name__ == "__main__":
    wav = r"D:\Projects\ai-video-studio\models\reference_audio\my_voice_raw.wav"
    out = r"D:\Projects\ai-video-studio\models\reference_audio\slices"
    segs = slice_audio_local(wav, out)
    for s, d in segs[:5]:
        print(f"  {os.path.basename(s)}: {d:.2f}s")
