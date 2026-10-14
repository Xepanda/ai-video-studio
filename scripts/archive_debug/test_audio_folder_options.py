import asyncio
from playwright.async_api import async_playwright

options = [
    ("empty", ""),
    ("dot", "."),
    ("root_dir", "/content/GPT-SoVITS"),
    ("slicer_opt", "output/slicer_opt"),
    ("full_slicer_opt", "/content/GPT-SoVITS/output/slicer_opt"),
]

async def test_options():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
        page = await b.new_page()
        print("Navigating to Gradio...", flush=True)
        await page.goto("https://a6ff877b71b35e5521.gradio.live/", timeout=60000)
        await page.wait_for_timeout(3000)
        
        await page.locator("button", has_text="1-GPT-SOVITS-TTS").click()
        await page.wait_for_timeout(2000)
        
        # Select v2
        v2_label = page.locator("label", has_text="v2").filter(has_not_text="v2Pro")
        for i in range(await v2_label.count()):
            txt = (await v2_label.nth(i).inner_text()).strip()
            if txt == "v2":
                await v2_label.nth(i).click()
                print("Selected v2 radio", flush=True)
                break
        await page.wait_for_timeout(1000)
        
        # Exp name
        exp = page.locator("label:has-text('*Experiment/model name') >> .. >> input, label:has-text('*Experiment/model name') >> .. >> textarea").first
        await exp.fill("epanda_voice")
        
        # Labelling file
        lab = page.locator("label:has-text('*Text labelling file') >> .. >> input, label:has-text('*Text labelling file') >> .. >> textarea").first
        await lab.fill("output/asr_opt/slicer_opt.list")
        
        # GPU to 0
        gpus = page.locator("label:has-text('GPU number is separated by') >> .. >> input, label:has-text('GPU number is separated by') >> .. >> textarea")
        for i in range(await gpus.count()):
            field = gpus.nth(i)
            if await field.is_visible():
                await field.fill("0")

        # First terminate any running 1a if close button exists
        close1a = page.locator("button:has-text('Close Tokenization & BERT Feature Extraction')").first
        if await close1a.is_visible():
            print("Found Close 1Aa button, clicking to terminate...", flush=True)
            await close1a.click()
            await page.wait_for_timeout(2000)

        for name, folder in options:
            print(f"\n=== Testing Audio Dataset Folder option: '{name}' ('{folder}') ===", flush=True)
            aud = page.locator("label:has-text('*Audio dataset folder') >> .. >> input, label:has-text('*Audio dataset folder') >> .. >> textarea").first
            await aud.fill(folder)
            await page.wait_for_timeout(500)
            
            # Click Open 1Aa
            btn1a = page.locator("button:has-text('Open Tokenization & BERT Feature Extraction')").first
            if not await btn1a.is_visible():
                # Maybe it is close button
                close_btn = page.locator("button:has-text('Close Tokenization & BERT Feature Extraction')").first
                if await close_btn.is_visible():
                    await close_btn.click()
                    await page.wait_for_timeout(1000)
                    
            await btn1a.click()
            print("  Clicked Open 1Aa! Waiting 8s...", flush=True)
            for s in range(5):
                await page.wait_for_timeout(2000)
                txt1a = page.locator("label:has-text('Tokenization & BERT Feature Extraction Process Output Information') >> .. >> textarea").first
                val = await txt1a.input_value() if await txt1a.count() > 0 else ""
                print(f"  [{(s+1)*2}s] 1Aa output: {val.strip()}", flush=True)
                if "success" in val.lower() or "finish" in val.lower() or "done" in val.lower():
                    print(f"  -> SUCCESS with folder='{folder}'!", flush=True)
                    await page.screenshot(path=f"D:/Projects/ai-video-studio/success_{name}.png")
                    await b.close()
                    return
                if "occupying" in val.lower() or "fail" in val.lower() or "error" in val.lower():
                    break
            
            # Terminate if needed
            close_btn = page.locator("button:has-text('Close Tokenization & BERT Feature Extraction')").first
            if await close_btn.is_visible():
                await close_btn.click()
                await page.wait_for_timeout(1500)

        await b.close()

if __name__ == "__main__":
    asyncio.run(test_options())
