# BunnyBot 🐰💕✨

This project is an AI virtual assistant chatbot that uses speech recognition, text-to-speech, and voice activation detection to have a conversation with you. It is locally hosted and uses an open source LLM using `LM Studio`, `faster-whisper` for speech-to-text, and `openai-edge-tts` for text-to-speech and `Flask` for the web interface in a browser.

The project was a way for me to get back into learning coding again by learning how to use Python and studying the general functions and usage of LLMs within NLP. The project has slowly become a hybrid study on the use and understanding of the English language just as much as it is the study of LLMs.

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

### Future Features 🚀

There are many features I plan to add to this app in the future, with no specific timeline in mind. There are many things to learn, and the order in which features are developed and released is not set in stone, nor will any features be guaranteed to be added, released, or kept in the future.

Some of the features I plan to add include:

+ **Voice Activated Commands**: The ability to use voice commands to control the app, such as commands and phrases to get the chatbot to listen, similar to how you might use a voice assistant on your phone or how you would address someone in person to get their attention.
+ **Multilingual Conversation**: I am fluently bilingual (English and French) so I thought it could be cool if my chatbot could flip flop between the two languages in the same I can do in person. This could also be useful in assistant type tasks in the future, such as working on documents and emails, spell check, reading for me, etc.
+ **Sentiment Analysis**: The ability to analyze the sentiment of the conversation and provide feedback to the user, such as whether the conversation is positive, negative, or neutral. I want to implement it in two ways, one would be where the chatbot might "grade" the users sentiment, and react accordingly. The other would be where sentiment analysis could be used to "grade" the chatbot's sentiment and I can use that for if and when I try to make an animated character/image for it. Example, if the chatbot is acting happy I can have it smile as a visual queue, obtained via the sentiment analysis.
+ **Memory Module for Long Term Memory**: AI chatbots and LLMs don't store chats or "remember" things outside of the context window. Close the chat and it's gone forever. I would like to implement something where if it is important and relevant information, the AI would be able to store it (likely in a vector store using SQL) and retrieve it when needed. This would be useful for things like reminders, notes, or anything that might be important to the user. Could also be used for preferences, likes and dislikes, important dates, things the AI thinks it should note down and remember about the user and generalized chat summaries, to help it condense and contextualize past conversations.
+ **Functions**: Practical functions that can be used via voice controls such as asing it to remember/memorize something (add to Memory), ask if it remembers something (Memory search), delete/update/change a memory, set reminders/timers, write notes, and whatever else might be useful to the user.

These are just a few ideas. Everything is up in the air for now.
