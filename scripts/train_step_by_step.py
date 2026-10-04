import asyncio
import time
import sys
from playwright.async_api import async_playwright

GRADIO_URL = "https://2d81a9ff9cf72026f9.gradio.live/"

async def wait_for_process(page, label_pattern, timeout=180, check_name="Task"):
    print(f"[{check_name}] Waiting for completion (timeout {timeout}s)...", flush=True)
    start = time.time()
    last_msg = ""
    while time.time() - start < timeout:
        await page.wait_for_timeout(3000)
        box = page.locator(f"label:has-text('{label_pattern}') >> .. >> textarea").first
        val = (await box.input_value()).strip() if await box.count() > 0 else ""
        elapsed = int(time.time() - start)
        if val != last_msg:
            print(f"  [{check_name} +{elapsed}s] {val}", flush=True)
            last_msg = val
        if any(w in val.lower() for w in ["success", "finish", "done", "已完成", "完成", "saved"]):
            print(f"[{check_name}] SUCCESS in {elapsed}s!", flush=True)
            return True
        if "fail" in val.lower() or "error" in val.lower() or "失败" in val:
            print(f"[{check_name}] FAILED: {val}", flush=True)
            return False
    print(f"[{check_name}] TIMEOUT after {timeout}s", flush=True)
    return False

async def run():
    print("==================================================", flush=True)
    print("   GPT-SoVITS E2E STEP-BY-STEP AUTOMATION START   ", flush=True)
    print("==================================================", flush=True)
    
    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = await b.new_page()
        page.set_default_timeout(60000)
        
        print(f"\n>>> Step 0: Opening Gradio WebUI at {GRADIO_URL}...", flush=True)
        await page.goto(GRADIO_URL, timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Navigate to Tab 1
        print(">>> Switching to Tab '1-GPT-SOVITS-TTS'...", flush=True)
        tab_btn = page.locator("button", has_text="1-GPT-SOVITS-TTS").first
        await tab_btn.click()
        await page.wait_for_timeout(2000)
        
        # 1. Switch to v2 model
        print(">>> Selecting model version 'v2'...", flush=True)
        v2_label = page.locator("label", has_text="v2").filter(has_not_text="v2Pro")
        for i in range(await v2_label.count()):
            txt = (await v2_label.nth(i).inner_text()).strip()
            if txt == "v2":
                await v2_label.nth(i).click()
                print("  -> Radio 'v2' selected successfully.", flush=True)
                break
        await page.wait_for_timeout(1500)
        
        # 2. Set experiment name
        print(">>> Setting Experiment name to 'epanda_voice'...", flush=True)
        exp = page.locator("label:has-text('*Experiment/model name') >> .. >> input, label:has-text('*Experiment/model name') >> .. >> textarea").first
        await exp.fill("epanda_voice")
        
        # 3. Text labelling file
        print(">>> Setting Text labelling file to 'output/asr_opt/slicer_opt.list'...", flush=True)
        lab = page.locator("label:has-text('*Text labelling file') >> .. >> input, label:has-text('*Text labelling file') >> .. >> textarea").first
        await lab.fill("output/asr_opt/slicer_opt.list")
        
        # 4. Audio dataset folder
        print(">>> Setting Audio dataset folder to 'output/slicer_opt'...", flush=True)
        aud = page.locator("label:has-text('*Audio dataset folder') >> .. >> input, label:has-text('*Audio dataset folder') >> .. >> textarea").first
        await aud.fill("output/slicer_opt")
        
        # 5. Set GPU to 0
        gpus = page.locator("label:has-text('GPU number is separated by') >> .. >> input, label:has-text('GPU number is separated by') >> .. >> textarea")
        for i in range(await gpus.count()):
            field = gpus.nth(i)
            if await field.is_visible():
                await field.fill("0")
        print("  -> All visible GPU fields set to '0'.", flush=True)
        
        # Reset any active close buttons
        for btn in await page.locator("button:has-text('Close')").all():
            if await btn.is_visible():
                txt = await btn.inner_text()
                print(f"  -> Resetting active button: {txt}", flush=True)
                await btn.click()
                await page.wait_for_timeout(1000)
                
        # -------------------------------------------------------------
        # STEP 1Aa: Tokenization & BERT Feature Extraction
        # -------------------------------------------------------------
        print("\n>>> [1Aa] Starting Tokenization & BERT Feature Extraction...", flush=True)
        btn1a = page.locator("button:has-text('Open Tokenization & BERT Feature Extraction')").first
        await btn1a.click()
        ok1a = await wait_for_process(page, "Tokenization & BERT Feature Extraction Process", timeout=120, check_name="1Aa-BERT")
        if not ok1a:
            await page.screenshot(path="D:/Projects/ai-video-studio/fail_1aa_new.png")
            await b.close()
            return False
            
        # -------------------------------------------------------------
        # STEP 1Ab: Speech SSL Feature Extraction
        # -------------------------------------------------------------
        print("\n>>> [1Ab] Starting Speech SSL Feature Extraction...", flush=True)
        btn1b = page.locator("button:has-text('Open Speech SSL Feature Extraction')").first
        await btn1b.click()
        ok1b = await wait_for_process(page, "Speech SSL Feature Extraction Process", timeout=120, check_name="1Ab-SSL")
        if not ok1b:
            await page.screenshot(path="D:/Projects/ai-video-studio/fail_1ab_new.png")
            await b.close()
            return False
            
        # -------------------------------------------------------------
        # STEP 1Ac: Semantics Token Extraction
        # -------------------------------------------------------------
        print("\n>>> [1Ac] Starting Semantics Token Extraction...", flush=True)
        btn1c = page.locator("button:has-text('Open Semantics Token Extraction')").first
        await btn1c.click()
        ok1c = await wait_for_process(page, "Semantics Token Extraction Process", timeout=120, check_name="1Ac-Semantic")
        if not ok1c:
            await page.screenshot(path="D:/Projects/ai-video-studio/fail_1ac_new.png")
            await b.close()
            return False
            
        print("\n>>> [Step 1A ALL DONE] Dataset formatting is 100% complete! <<<", flush=True)
        await page.screenshot(path="D:/Projects/ai-video-studio/1a_complete_new.png")
        await page.wait_for_timeout(2000)
        
        # -------------------------------------------------------------
        # STEP 1Ba: SoVITS Fine-Tuning
        # -------------------------------------------------------------
        print("\n>>> [1Ba] Switching to 1B-Fine-Tuning tab...", flush=True)
        await page.locator("button", has_text="1B-Fine-Tuning").first.click()
        await page.wait_for_timeout(2000)
        
        print(">>> Starting SoVITS Training (8 Epochs)...", flush=True)
        btn_sov = page.locator("button:has-text('Open SoVITS Training')").first
        await btn_sov.click()
        ok_sov = await wait_for_process(page, "SoVITS Training Process", timeout=420, check_name="1Ba-SoVITS")
        if not ok_sov:
            await page.screenshot(path="D:/Projects/ai-video-studio/fail_sovits_new.png")
            await b.close()
            return False
            
        await page.screenshot(path="D:/Projects/ai-video-studio/sovits_trained_new.png")
        await page.wait_for_timeout(2000)
        
        # -------------------------------------------------------------
        # STEP 1Bb: GPT Fine-Tuning
        # -------------------------------------------------------------
        print("\n>>> [1Bb] Starting GPT Training (15 Epochs)...", flush=True)
        btn_gpt = page.locator("button:has-text('Open GPT Training')").first
        await btn_gpt.click()
        ok_gpt = await wait_for_process(page, "GPT Training Process", timeout=420, check_name="1Bb-GPT")
        if not ok_gpt:
            await page.screenshot(path="D:/Projects/ai-video-studio/fail_gpt_new.png")
            await b.close()
            return False
            
        await page.screenshot(path="D:/Projects/ai-video-studio/training_finished_new.png")
        print("\n==================================================", flush=True)
        print("   ALL TRAINING COMPLETE! WEIGHTS EXPORTED!       ", flush=True)
        print("==================================================", flush=True)
        await b.close()
        return True

if __name__ == "__main__":
    success = asyncio.run(run())
    sys.exit(0 if success else 1)
