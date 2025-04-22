# BunnyBot 🐰💕✨

This project is a AI virtual assistant chatbot that uses speech recognition, text-to-speech, and voice activation detection to have a conversation with you. It is locally hosted and uses an open source LLM using `LM Studio`, `faster-whisper` for speech-to-text, and `openai-edge-tts` for text-to-speech and `Flask` for the web interface in a browser.

The project was a way for me to get back into learning coding again by learning how to use Python and studying the general functions and usage of LLMs within NLP. The project has slowly become a hybrid study on the use and understanding of the English language just as much as it is the study of LLMs.

## Version 0.1.0 Notes 📝 (April 21, 2025): Initial release of the app. Very basic, but stable.

### Features 🎉

+ **Speech to Text**: Transcribes audio from a microphone into text using the `faster-whisper` library.
+ **Text to Speech**: Converts text into speech using the `openai-edge-tts` library.
+ **Voice Activated Detection**: The LLM self-prompts and tries to carry the conversation alone to avoid awkward silence, but will not self prompt if the user is speaking. Transcription only happens when VAD occurs.
+ **Web Interface**: The web interface with `Flask` allows users to see the transcription and read to the reply in real-time in a browser window. Also gives you buttons to turn transcription/mic on/off, and clear the conversation in the browser window. (Does not delete conversation history with the LLM, you'd need to restart the app for that.)

### Future Features 🚀

There are many features I plan to add to this app in the future, with no specific timeline in mind. There are many things to learn, and the order in which features are developed and released is not set in stone, nor will any features be guaranteed to be added, released, or kept in the future.

Some of the features I plan to add include:

+ **Voice Activated Commands**: The ability to use voice commands to control the app, such as commands and phrases to get the chatbot to listen, similar to how you might use a voice assistant on your phone or how you would address someone in person to get their attention.
+ **Multilingual Conversation**: I am fluently bilingual (English and French) so I thought it could be cool if my chatbot could flip flop between the two languages in the same I can do in person. This could also be useful in assistant type tasks in the future, such as working on documents and emails, spell check, reading for me, etc.
+ **Sentiment Analysis**: The ability to analyze the sentiment of the conversation and provide feedback to the user, such as whether the conversation is positive, negative, or neutral. I want to implement it in two ways, one would be where the chatbot might "grade" the users sentiment, and react accordingly. The other would be where sentiment analysis could be used to "grade" the chatbot's sentiment and I can use that for if and when I try to make an animated character/image for it. Example, if the chatbot is acting happy I can have it smile as a visual queue, obtained via the sentiment analysis.
+ **Memory Module for Long Term Memory**: AI chatbots and LLMs don't store chats or "remember" things outside of the context window. Close the chat and it's gone forever. I would like to implement something where if it is important and relevant information, the AI would be able to store it (likely in a vector store using SQL) and retrieve it when needed. This would be useful for things like reminders, notes, or anything that might be important to the user. Could also be used for preferences, likes and dislikes, important dates, things the AI thinks it should note down and remember about the user and generalized chat summaries, to help it condense and contextualize past conversations.
+ **Functions**: Practical functions that can be used via voice controls such as asing it to remember/memorize something (add to Memory), ask if it remembers something (Memory search), delete/update/change a memory, set reminders/timers, write notes, and whatever else might be useful to the user.

These are just a few ideas. Everything is up in the air for now.
