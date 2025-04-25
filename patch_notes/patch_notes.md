## Version 0.3.4 Notes 📝 (April 24, 2023): User profiles and long term memory!

+ [User Profiles](#user_profiles) User Profiles
+ [Long Term Memory](#long_term_memory) Long Term Memory
+ [UI Improvements](#ui_improvements) UI Improvements
+ [Bug Fixes](#bug_fixes) Bug Fixes

### <a name="user_profiles"></a>User Profiles! 👥
Integrated a user profile module, enabling the app to save relevant information about the user to a json file. This includes things like preferences (likes and dislikes), hobbies, interests, important dates, and anything else that might be relevant to the user. The app will use this information to make the conversation more personalized to the user.

### <a name="long_term_memory"></a>Long Term Memory! 🧠
One of the biggest "problems" with LLMs as chatbots is the limitations of the context window, as well as not being able to retain memories from one conversation to the next. Implementing long term memory would allow the AI to remember things across conversations, be able to keep conversations going and be more useful in a conversation. 

At the moment I only have the base framework set up, with a simple memory module, and a preferences extraction module.

### <a name="ui_improvements"></a>UI Improvements! 💻
Some improvements and additions have been made to the UI, including:

+ A more visually pleasing UI, with a side bar.
+ Added more buttons for better control (listening on/off, timer on/off, clear chat, end chat)
+ Added manual User ID input for changing the user profile.
+ Added names to the chat bubbles.

There are still more improvements to make as I go along, but this is a good start.
Will likely add light/dark mode and other things but what matters most right now is that I have a working UI that allows a visual text output of the chat and ways to control/test it.

### <a name="bug_fixes"></a>Bug Fixes! 🐛
Some minor bug fixes/corrections have been made, including:

+ Fixed the self prompt timer so that it waits for audio to finish playing before restarting.
+ Fixed the self prompt timer for the LLM so it doesn't self prompt when the user is speaking/sound is detected.
+ Fixed the TTS queue so that new audio waits for previous audio to finish before playing (preventing cut off).
+ While TTS is playing, STT still gathers transcriptions and consolodates them into one, to avoid creating too many transcriptions and a backlog.

## Version 0.2.1 Notes 📝 (April 22, 2023): Voice commands!

### Adding Voice Commands! 🔊
I have integrated the very bare bones of a module for the management and usage of **voice commands** for my virtual assistant. So far, I have only added the ability to use some phrases to get the attention of the chatbot via using the command as a part of prompt engineering.

#### Some of the phrases:
+ Hey Bunny
+ Okay Bunny
+ Bunny
+ Hey Bun Bun
+ and a few more

### Bug Fixes 🐛

#### STT and TTS Improvements:
+ Removed text streaming for both live transcriptions via STT as well as the live streaming text from the LLM response to reduce latency.
+ Optimized STT settings to reduce lag and latency when transcribing longer audio. 
+ Made sure TTS queue does not cut off currently playing audio and bump up the next item in queue.
+ Optimized the VAD settings to wait 1.5 seconds of silence before deciding to send transctription to the LLM. (Was too hasty.)
+ Added a confidence filter for STT to significantly reduce the amount of "false positives" where it mistakens white noise for speech, trying to fill it in with "Thank you.", "Thank you for watching", etc.

#### Self Prompt Fixes:
+ Fixed the self prompt timer for the LLM so it doesn't self prompt when the user is speaking/sound is detected.
+ Fixed the self prompt timer so that it waits for audio to finish playing before restarting.

#### UI Improvements:
+ Removed the unnecessary div box from the HTML.
+ Removed live streaming of text, messages now display once they are done.

And other general minor edits and bug fixes.

## Version 0.1.0 Notes 📝 (April 21, 2025): Initial release of the app. Very basic but stable.
***
### Features 🎉

+ **Speech to Text**: Transcribes audio from a microphone into text using the `faster-whisper` library.
+ **Text to Speech**: Converts text into speech using the `openai-edge-tts` library.
+ **Voice Activated Detection**: The LLM self-prompts and tries to carry the conversation alone to avoid awkward silence, but will not self prompt if the user is speaking. Transcription only happens when VAD occurs.
+ **Web Interface**: The web interface with `Flask` allows users to see the transcription and read to the reply in real-time in a browser window. Also gives you buttons to turn transcription/mic on/off, and clear the conversation in the browser window. (Does not delete conversation history with the LLM, you'd need to restart the app for that.)