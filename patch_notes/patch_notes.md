## Version 0.4.4 Notes 📝 (April 26, 2023): Browser UI Update!
Overhauled the browser UI to make it more visually pleasing and user friendly.

+ [Buttons](#buttons) Buttons
+ [Chat Window](#chat_window) Chat Window Improvements
+ [Text Input](#text_input) Text Input Improvements
+ [User Profile Management](#user_profile_management) User Profile Management
+ [Style Improvements](#style_improvements) Style Improvements
+ [Bug Fixes](#bug_fixes) Bug Fixes

### <a name="buttons"></a>Buttons! 🔘
Updated the buttons to be more visually pleasing and user friendly. The Listening (mic) and self-prompting (timer) buttons now change colour to indicate if that feature is on or off, and the status of these features are clearly visible to the user just above the buttons.

### <a name="chat_window"></a>Chat Window Improvements! 💬
The chat window now has a scrollbar to make it easier to read the conversation, and the chat bubbles are now a bit larger and more visually pleasing. A scroll to bottom button has been added to the chat window to make it easier to return to the current position in the conversation. The chat window now scales with the size of the text input.

### <a name="text_input"></a>Text Input Improvements! ⌨️
Added a text input feature to allow for typing messages to the AI, which will continue to use TTS to reply to the user. Text input now scales with the size of the written message for easier readability, and a scrollbar was added in case it gets too long. Send button sends the text message directly to the AI in the same way as voice input, in the same queue. Both text input and STT can be used at the same time.

### <a name="user_profile_management"></a>User Profile Management! 👥
Manually input and switch the user profile, allowing for the AI to be more personal in conversation as well as "remember" things relevant to each different user.

### <a name="style_improvements"></a>Style Improvements! 🎨
Updated the style of the UI to be more visually pleasing and user friendly with the help of updates to the html, css and javascript files. Added AJAX for better seamless functionality. More UI improvements to come in the future, such as dark/light mode and possibly other themes and buttons as needed.
### <a name="bug_fixes"></a>Bug Fixes! 🐛
+ Fixed a bug where the chat window would not allow scrolling while chat was open.
+ Fixed a bug where ending chat would redirect to a blank html page with only the "chat ended" status.
+ Fixed a bug where AI messages would sometimes duplicate or attempt to do live text response streaming at the same time as a final AI message.
+ Fixed a bug where the chat window would flash white and refresh too often when a new message was added to the chat window.
+ Other minor updates.

## Version 0.3.4 Notes 📝 (April 24, 2023): User profiles and long term memory!

+ [User Profiles](#user_profiles) User Profiles
+ [Long Term Memory](#long_term_memory) Long Term Memory
+ [UI Improvements](#ui_improvements) UI Improvements
+ [Bug Fixes](#bug_fixes2) Bug Fixes

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

### <a name="bug_fixes2"></a>Bug Fixes! 🐛
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