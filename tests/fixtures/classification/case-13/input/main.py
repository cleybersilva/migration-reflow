"""Exemplo sintético; somente parsear, nunca executar durante a migração."""

import pyautogui


def launch_entry():
    pyautogui.hotkey("alt", "tab")
    pyautogui.click(320, 240)
    pyautogui.write("lote")
    pyautogui.press("enter")
