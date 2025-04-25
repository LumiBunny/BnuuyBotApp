# BunnyBot 🐰💕✨

This project is an AI virtual assistant chatbot that uses speech recognition, text-to-speech, and voice activation detection to have a conversation with you. It is locally hosted and uses an open source LLM using `LM Studio`, `faster-whisper` for speech-to-text, and `openai-edge-tts` for text-to-speech and `Flask` for the web interface in a browser.

The project was a way for me to get back into learning coding again by learning how to use Python and studying the general functions and usage of LLMs within NLP. The project has slowly become a hybrid study on the use and understanding of the English language just as much as it is the study of LLMs.

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

### Future Features 🚀

There are many features I plan to add to this app in the future, with no specific timeline in mind. There are many things to learn, and the order in which features are developed and released is not set in stone, nor will any features be guaranteed to be added, released, or kept in the future.

Some of the features I plan to add include:

+ **Voice Activated Commands**: The ability to use voice commands to control the app, such as commands and phrases to get the chatbot to listen, similar to how you might use a voice assistant on your phone or how you would address someone in person to get their attention.
+ **Multilingual Conversation**: I am fluently bilingual (English and French) so I thought it could be cool if my chatbot could flip flop between the two languages in the same I can do in person. This could also be useful in assistant type tasks in the future, such as working on documents and emails, spell check, reading for me, etc.
+ **Sentiment Analysis**: The ability to analyze the sentiment of the conversation and provide feedback to the user, such as whether the conversation is positive, negative, or neutral. I want to implement it in two ways, one would be where the chatbot might "grade" the users sentiment, and react accordingly. The other would be where sentiment analysis could be used to "grade" the chatbot's sentiment and I can use that for if and when I try to make an animated character/image for it. Example, if the chatbot is acting happy I can have it smile as a visual queue, obtained via the sentiment analysis.
+ **Memory Module for Long Term Memory**: AI chatbots and LLMs don't store chats or "remember" things outside of the context window. Close the chat and it's gone forever. I would like to implement something where if it is important and relevant information, the AI would be able to store it (likely in a vector store using SQL) and retrieve it when needed. This would be useful for things like reminders, notes, or anything that might be important to the user. Could also be used for preferences, likes and dislikes, important dates, things the AI thinks it should note down and remember about the user and generalized chat summaries, to help it condense and contextualize past conversations.
+ **Functions**: Practical functions that can be used via voice controls such as asing it to remember/memorize something (add to Memory), ask if it remembers something (Memory search), delete/update/change a memory, set reminders/timers, write notes, and whatever else might be useful to the user.

These are just a few ideas. Everything is up in the air for now.
