import pyautogui
import time
""" 
Automatically input text into a textbox.
"""

def auto_input(text: str, delay: int = 0):
    """
    Input the contents of `text` into whatever text box we have selected.
    
    Args:
        text: Determines what content to write into a textbox.
        delay: Determines how long to wait before writing said text
        
    Precondition:
        For this function to appropriately work, Ghostty must have appropriate computer access.
        You can give Ghostty this by going to System Settings > Privacy & Security > Accessibility.
        Toggle on Ghostty before running this script. MAKE SURE TO TOGGLE GHOSTTY OFF WHEN YOU'RE DONE.

    """
    
    time.sleep(delay)
    pyautogui.write(text)
    
if __name__ == "__main__":
    auto_input("Football, known in the states as soccer, is a really cool sport that many adults and children alike enjoy and cherish \n.")