"""Simple test to verify translation works in Notepad."""
import subprocess
import time
import pyperclip
import pyautogui

def main():
    print("=" * 60)
    print("TRANSLATION TEST - 3 ITERATIONS")
    print("=" * 60)
    
    print("\nOpening Notepad...")
    subprocess.Popen(['notepad.exe'])
    time.sleep(2)
    
    test_texts = [
        "Hello world",
        "Good morning",
        "How are you today",
    ]
    
    passed = 0
    failed = 0
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n[Test {i}/3] EN->ZH: {text}")
        
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        
        print("  Triggering translation (Ctrl+Shift+Space)...")
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('shift')
        pyautogui.press('space')
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        
        print("  Waiting for translation (15s)...")
        time.sleep(15)
        
        print("  Reading result...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        result = pyperclip.paste()
        
        if result != text and len(result) > 0 and result != '':
            print(f"  PASS - Got: {result}")
            passed += 1
        else:
            print(f"  FAIL - Got: {result}")
            failed += 1
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: Passed={passed}, Failed={failed}")
    print("=" * 60)
    
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.3)
    pyautogui.press('n')
    
    return failed == 0

if __name__ == "__main__":
    main()
