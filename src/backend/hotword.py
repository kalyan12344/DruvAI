# import threading
# import speech_recognition as sr
# import time

# def listen_for_hotword(trigger_callback):
#     recognizer = sr.Recognizer()
#     mic = sr.Microphone()

#     with mic as source:
#         recognizer.adjust_for_ambient_noise(source)

#     print("🎧 Listening for 'Hey Druv'...")

#     while True:
#         with mic as source:
#             try:
#                 audio = recognizer.listen(source, timeout=3)
#                 text = recognizer.recognize_google(audio).lower()
#                 print("You said:", text)
#                 if "hey dhruv" in text:
#                     print("🎤 Wake word detected!")
#                     trigger_callback()
#             except (sr.UnknownValueError, sr.WaitTimeoutError):
#                 continue
#             except Exception as e:
#                 print("🎙️ Error:", e)

# # 👇 Call this in background
# def start_hotword_thread(trigger_callback):
#     t = threading.Thread(target=listen_for_hotword, args=(trigger_callback,), daemon=True)
#     t.start()
