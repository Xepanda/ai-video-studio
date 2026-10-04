import time
import sys
from gradio_client import Client

GRADIO_URL = "https://2d81a9ff9cf72026f9.gradio.live/"
EXP_NAME = "epanda_voice"

def main():
    print("==================================================", flush=True)
    print("   GPT-SoVITS STAGE 1B: MODEL FINE-TUNING        ", flush=True)
    print("==================================================", flush=True)
    
    print(f"\n[INIT] Connecting to Gradio at {GRADIO_URL}...", flush=True)
    client = Client(GRADIO_URL)
    print("[INIT] Connected successfully!", flush=True)
    
    # -------------------------------------------------------------
    # STEP 1Ba: SoVITS Fine-Tuning (8 Epochs)
    # -------------------------------------------------------------
    print("\n>>> [1Ba] Submitting SoVITS Fine-Tuning (8 Epochs, Batch Size 7)...", flush=True)
    job_sov = client.submit(
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
    
    start_sov = time.time()
    while not job_sov.done():
        time.sleep(5)
        elapsed = int(time.time() - start_sov)
        print(f"  [1Ba SoVITS Training] Elapsed: {elapsed}s...", flush=True)
        
    res_sovits = job_sov.result()
    sovits_out = res_sovits[0] if isinstance(res_sovits, (list, tuple)) else res_sovits
    print(f"\n[1Ba] SUCCESS in {int(time.time() - start_sov)}s! Result: {sovits_out}", flush=True)
    time.sleep(3)
    
    # -------------------------------------------------------------
    # STEP 1Bb: GPT Fine-Tuning (15 Epochs)
    # -------------------------------------------------------------
    print("\n>>> [1Bb] Submitting GPT Fine-Tuning (15 Epochs, Batch Size 7)...", flush=True)
    job_gpt = client.submit(
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
    
    start_gpt = time.time()
    while not job_gpt.done():
        time.sleep(5)
        elapsed = int(time.time() - start_gpt)
        print(f"  [1Bb GPT Training] Elapsed: {elapsed}s...", flush=True)
        
    res_gpt = job_gpt.result()
    gpt_out = res_gpt[0] if isinstance(res_gpt, (list, tuple)) else res_gpt
    print(f"\n[1Bb] SUCCESS in {int(time.time() - start_gpt)}s! Result: {gpt_out}", flush=True)
    time.sleep(3)
    
    # -------------------------------------------------------------
    # Verify Exported Weights
    # -------------------------------------------------------------
    print("\n>>> [VERIFY] Checking Exported Model Weights...", flush=True)
    choices = client.predict(api_name='/change_choices')
    print("Available SoVITS Weights:", choices[0] if len(choices) > 0 else "None", flush=True)
    print("Available GPT Weights:", choices[1] if len(choices) > 1 else "None", flush=True)
    
    print("\n==================================================", flush=True)
    print("   ALL TRAINING COMPLETE! WEIGHTS EXPORTED!       ", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    main()
