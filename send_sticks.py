import vgamepad as vg

gamepad = vg.VX360Gamepad()

gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)  # press the A button
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)  # press the left hat button

gamepad.update()  # send the updated state to the computer

# (...) A and left hat are pressed...

gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)  # release the A button

gamepad.update()  # send the updated state to the computer

# (...) left hat is still pressed...

del gamepad