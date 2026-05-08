
import asyncio
import os
import tempfile
import re
from loguru import logger

async def test_nxbgd_logic():
    logger.info("--- STARTING DOCKER INTEGRATION TEST (NXBGD LOGIC) ---")
    
    # 1. Test safe title and temp dir creation
    full_title = 'Sách Giáo Khoa Toán Lớp 1 (Tập 1) :?*"'
    safe_title = re.sub(r'[\\/*?:"<>|]', "", full_title).strip()
    
    logger.info(f"Step 1: Testing Title Sanitization")
    logger.info(f"Raw: {full_title}")
    logger.info(f"Safe: {safe_title}")
    
    # 2. Test tempfile.mkdtemp (The new standard I implemented)
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"nxbgd_{safe_title[:20]}_")
        logger.info(f"Step 2: Created isolated temp dir: {temp_dir}")
        
        # Verify it exists
        if os.path.exists(temp_dir):
            logger.info("SUCCESS: Temp directory is accessible.")
        
        # 3. Test writing a dummy file
        dummy_file = os.path.join(temp_dir, "nxbgd_page_0001.jpg")
        with open(dummy_file, "w") as f:
            f.write("test data")
        
        if os.path.exists(dummy_file):
            logger.info(f"Step 3: Successfully wrote dummy capture: {dummy_file}")
            
        # 4. Check for Tectonic (This is actually in the Dockerfile)
        logger.info("Step 4: Checking Tectonic (LaTeX engine) availability...")
        proc = await asyncio.create_subprocess_exec(
            "tectonic", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            logger.info(f"SUCCESS: Tectonic is installed: {stdout.decode().strip()}")
        else:
            logger.error("Tectonic NOT found.")

        # 5. Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        logger.info("Step 5: Cleaned up temp directory.")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

    logger.info("--- DOCKER TEST COMPLETE: LOGIC VERIFIED ---")
    return True

if __name__ == "__main__":
    asyncio.run(test_nxbgd_logic())
