import time
import sys
from gradio_client import Client

GRADIO_URL = "https://2d81a9ff9cf72026f9.gradio.live/"
EXP_NAME = "epanda_voice"

def main():
    print("==================================================", flush=True)
    print("   GPT-SoVITS AUTOMATED PIPELINE EXECUTION        ", flush=True)
    print("==================================================", flush=True)
    
    print(f"\n[INIT] Connecting to Gradio at {GRADIO_URL}...", flush=True)
    client = Client(GRADIO_URL)
    print("[INIT] Connected successfully!", flush=True)
    print("[STATUS] 1Aa (BERT) and 1Ab (Speech SSL) are already completed!", flush=True)
    
    # -------------------------------------------------------------
    # STEP 1Ac: Semantics Token Extraction
    # -------------------------------------------------------------
    print("\n>>> [1Ac] Starting Semantics Token Extraction...", flush=True)
    t0 = time.time()
    res_1c = client.predict(
        'v2',
        'output/asr_opt/slicer_opt.list',
        'output/slicer_opt',
        EXP_NAME,
        '0',
        'GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth',
        api_name='/open1c'
    )
    print(f"[1Ac] Completed in {int(time.time() - t0)}s: {res_1c}", flush=True)
    if "fail" in str(res_1c).lower() or "error" in str(res_1c).lower():
        print("[1Ac] ERROR: Semantics Token Extraction failed!", flush=True)
        sys.exit(1)
        
    print("\n>>> [DATASET FORMATTING COMPLETE] 1A (BERT, SSL, Semantic Tokens) 100% DONE! <<<", flush=True)
    
    # -------------------------------------------------------------
    # STEP 1Ba: SoVITS Fine-Tuning (8 Epochs)
    # -------------------------------------------------------------
    print("\n>>> [1Ba] Starting SoVITS Fine-Tuning (8 Epochs, Batch Size 7)...", flush=True)
    t0 = time.time()
    res_sovits = client.predict(
        'v2',
        7,
        8,
        EXP_NAME,
        0.4,
        True,
        True,
        4,
        '0',
        'GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth',
        'GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2D2333k.pth',
        False,
        '32',
        api_name='/open1Ba'
    )
    sovits_out = res_sovits[0] if isinstance(res_sovits, (list, tuple)) else res_sovits
    print(f"[1Ba] Completed in {int(time.time() - t0)}s: {sovits_out}", flush=True)
    
    # -------------------------------------------------------------
    # STEP 1Bb: GPT Fine-Tuning (15 Epochs)
    # -------------------------------------------------------------
    print("\n>>> [1Bb] Starting GPT Fine-Tuning (15 Epochs, Batch Size 7)...", flush=True)
    t0 = time.time()
    res_gpt = client.predict(
        7,
        15,
        EXP_NAME,
        False,
        True,
        True,
        5,
        '0',
        'GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt',
        api_name='/open1Bb'
    )
    gpt_out = res_gpt[0] if isinstance(res_gpt, (list, tuple)) else res_gpt
    print(f"[1Bb] Completed in {int(time.time() - t0)}s: {gpt_out}", flush=True)
    
    print("\n==================================================", flush=True)
    print("   ALL MODEL TRAINING COMPLETED SUCCESSFULLY!     ", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    main()
