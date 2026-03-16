"""
Automated test script for translation functionality.
Tests bidirectional translation with auto-retry on failure.
"""
import time
import subprocess
import pyautogui
import pyperclip
import sys

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

def open_notepad():
    subprocess.Popen(['notepad.exe'])
    time.sleep(2)

def type_text(text):
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

def select_all():
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)

def trigger_translation():
    pyautogui.keyDown('ctrl')
    time.sleep(0.15)
    pyautogui.keyDown('shift')
    time.sleep(0.15)
    pyautogui.press('space')
    time.sleep(0.15)
    pyautogui.keyUp('shift')
    time.sleep(0.15)
    pyautogui.keyUp('ctrl')
    time.sleep(15)

def get_text():
    select_all()
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    return pyperclip.paste()

def clear_notepad():
    select_all()
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.3)

def close_notepad():
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.5)
    pyautogui.press('n')
    time.sleep(0.5)

def run_single_test(test_text):
    try:
        clear_notepad()
        time.sleep(0.5)
        type_text(test_text)
        time.sleep(0.5)
        select_all()
        time.sleep(0.5)
        trigger_translation()
        time.sleep(1)
        result = get_text()
        success = result != test_text and len(result) > 0 and result.strip() != ''
        return success, result
    except Exception as e:
        return False, f"ERROR: {str(e)}"

def run_test_with_retry(iteration, test_text, max_retries=3):
    for attempt in range(max_retries):
        success, result = run_single_test(test_text)
        if success:
            return {
                'iteration': iteration,
                'input': test_text[:50],
                'output': result[:50] if result else '',
                'success': True,
                'attempts': attempt + 1
            }
        else:
            print(f"    Retry {attempt + 1}/{max_retries}...", end=" ")
            time.sleep(1)
    
    return {
        'iteration': iteration,
        'input': test_text[:50],
        'output': result[:50] if result else '',
        'success': False,
        'attempts': max_retries
    }

def main():
    print("=" * 60)
    print("AUTOMATED TRANSLATION TEST - 10 ITERATIONS")
    print("With auto-retry on failure (max 3 retries)")
    print("=" * 60)
    
    print("\nOpening Notepad...")
    open_notepad()
    time.sleep(3)
    
    english_texts = [
        "Hello, how are you today?",
        "The quick brown fox jumps over the lazy dog.",
        "This is a test of the translation system.",
        "Artificial intelligence is transforming the world.",
        "Please translate this sentence to Chinese."
    ]
    
    chinese_texts = [
        "你好，今天怎么样？",
        "人工智能正在改变世界。",
        "这是一个翻译系统测试。",
        "请将这句话翻译成英文。",
        "今天天气很好。"
    ]
    
    results = []
    success_count = 0
    fail_count = 0
    
    print("\nStarting 10 translation tests...")
    print("-" * 60)
    
    try:
        for i in range(1, 11):
            if i % 2 == 1:
                test_text = english_texts[i % len(english_texts)]
                direction = "EN->ZH"
            else:
                test_text = chinese_texts[i % len(chinese_texts)]
                direction = "ZH->EN"
            
            print(f"[{i:3d}/10] {direction} Testing: {test_text[:30]}...", end=" ")
            
            result = run_test_with_retry(i, test_text)
            results.append(result)
            
            if result['success']:
                success_count += 1
                print(f"PASS (attempts: {result['attempts']})")
            else:
                fail_count += 1
                print(f"FAIL - Output: {result['output']}")
                
                if fail_count >= 5:
                    print(f"\n*** Too many failures ({fail_count}), stopping test ***")
                    break
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    
    print("\nClosing Notepad...")
    try:
        close_notepad()
    except:
        pass
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {success_count}")
    print(f"Failed: {fail_count}")
    if len(results) > 0:
        print(f"Success rate: {success_count * 100 // len(results)}%")
    
    if fail_count > 0:
        print("\nFAILED TESTS:")
        print("-" * 60)
        for r in results:
            if not r['success']:
                print(f"  Iteration {r['iteration']}: Input='{r['input']}' Output='{r['output']}'")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    return fail_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
