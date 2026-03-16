"""
Automated test script for translation functionality.
Simple test that triggers translation and checks result.
"""
import time
import subprocess
import pyautogui
import pyperclip
import sys

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

def main():
    print("=" * 60)
    print("SIMPLE TRANSLATION TEST - 5 ITERATIONS")
    print("=" * 60)
    
    print("\nOpening Notepad...")
    subprocess.Popen(['notepad.exe'])
    time.sleep(3)
    
    test_texts = [
        ("Hello, how are you today?", "EN->ZH"),
        ("你好，今天怎么样？", "ZH->EN"),
        ("The quick brown fox jumps over the lazy dog.", "EN->ZH"),
        ("人工智能正在改变世界。", "ZH->EN"),
        ("This is a test.", "EN->ZH"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (text, direction) in enumerate(test_texts, 1):
        print(f"\n[Test {i}/5] {direction}: {text[:30]}...")
        
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        print("  Triggering translation...")
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('shift')
        pyautogui.press('space')
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        
        print("  Waiting for translation (20s)...")
        time.sleep(20)
        
        print("  Reading result...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        result = pyperclip.paste()
        
        if result != text and len(result) > 0:
            print(f"  PASS - Got: {result[:40]}...")
            passed += 1
        else:
            print(f"  FAIL - Got: {result[:40]}...")
            failed += 1
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.press('delete')
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: Passed={passed}, Failed={failed}")
    print("=" * 60)
    
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.5)
    pyautogui.press('n')
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
