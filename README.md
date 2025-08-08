# BunnyBot 🐰💕✨

Bunny Bot is an AI virtual assistant chat application. This project is made with `Python`. The app uses speech recognition (STT) using `faster-whisper`, text-to-speech using `openai-edge-tts`, and `Flask` for a browser-baseduser interface to display the chat log, as well as providing the option to text to the AI instead of using speech-to-text. The app uses a local open source LLM using LM Studio. The web interface not only features the chat log and chat box, but buttons for features and settings as well.

The project was a way for me to get back into learning coding again by learning how to use Python and studying the general functions and usage of LLMs within NLP. The project has slowly become a hybrid study on the use and understanding of the English language just as much as it is the study of LLMs.

## Version 0.5.1 Notes 📝 (August 8, 2025): 
LM Studio had some updates to their API, so I had to update the code to work with the new API. 

+ [Chat](#chat) Chat Updates
+ [Chat History](#chat_history) Chat History Updates
+ [Preferences](#preferences) Preference Extractor Updates
+ [UI Improvements](#ui_improvements) UI Improvements

### <a name="chat"></a>Chat Updates! 💬
LM Studio made some changes to their API allowing for a more streamlined way of handling chat history. The chat history is now handled internally via LM Studio, and no longer needs to be handled in the backend code. This makes chatting between user and LLM much more "natural" as the back and forth is now handled more seamlessly without the need to constantly append and save the chat history and make sure it is part of the LLM's context.

### <a name="chat_history"></a>Chat History Updates! 📚
Since the chat history and context of the conversation is now directly handled by LM Studio, the ChatHistory Class is now used for logging and saving copies of the chats for later use. These chats are auto saved as a json file. 

### <a name="preferences"></a>Preference Extractor Updates! 💕
Overhauled the preference extraction module. Many of the changes are to avoid repetitive calls and functions, as well as to make the code more efficient and easier to read. A combination of regex, spacy and sentiment analysis was used to extract preferences from the chat. The module was refined to attempt to handle compound sentences, understand the nuances of adverbs to enhance the user's feelings towards a preference, preferences that are implied by choice of words (example "I love pizza" implies that I like pizza, but saying "I like pizza" does not imply that I love it), handling negations, and handling of compound nouns (example: chocolate ice cream).

### <a name="ui_improvements"></a>UI Improvements! 💻
Small updates to the user UI in Flask to reflect some of the changes I have been making so far. Currently disabled user profiles, and temporarily removed other buttons. Added a button to allow the user to completely reset/restart the chat.

### Future Features 🚀

There are many features I plan to add to this app in the future, with no specific timeline in mind. There are many things to learn, and the order in which features are developed and released is not set in stone, nor will any features be guaranteed to be added, released, or kept in the future at this time.

Some of the features I plan to add include:

+ **Voice Activated Commands**: The ability to use voice commands to control the app, such as commands and phrases to get the chatbot to listen, similar to how you might use a voice assistant on your phone or how you would address someone in person to get their attention.
+ **Sentiment Analysis**: The ability to analyze the sentiment of the conversation and provide feedback to the user, such as whether the conversation is positive, negative, or neutral. I want to implement it in two ways, one would be where the chatbot might "grade" the users sentiment, and react accordingly. The other would be where sentiment analysis could be used to "grade" the chatbot's sentiment and I can use that for if and when I try to make an animated character/image for it. Example, if the chatbot is acting happy I can have it smile as a visual queue, obtained via the sentiment analysis.
+ **Memory Module for Long Term Memory**: AI chatbots and LLMs don't store chats or "remember" things outside of the context window. Close the chat and it's gone forever. I would like to implement something where if it is important and relevant information, the AI would be able to store it (likely in a vector store using SQL) and retrieve it when needed. This would be useful for things like reminders, notes, or anything that might be important to the user. Could also be used for preferences, likes and dislikes, important dates, things the AI thinks it should note down and remember about the user and generalized chat summaries, to help it condense and contextualize past conversations.
+ **Functions**: Practical functions that can be used via voice controls such as asing it to remember/memorize something (add to Memory), ask if it remembers something (Memory search), delete/update/change a memory, set reminders/timers, write notes, and whatever else might be useful to the user.

These are just a few ideas. Everything is up in the air for now.