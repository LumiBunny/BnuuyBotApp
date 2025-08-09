# BunnyBot 🐰💕✨

[Documentation](https://github.com/LumiBunny/BnuuyBotApp/wiki) • [Patch Notes](https://github.com/LumiBunny/BnuuyBotApp/wiki/1.-Patch-Notes) • Get Started

BunnyBot is an AI assistant chatbot application that enables speech-to-speech and text-based conversation with a locally hosted LLM. This project serves as a personal study on Python, LLMs, and the practical application of NLP.

## Features 🚀

* **Speech & Text Chat:** Interact with the AI using either your voice or a text chatbox.
* **Locally Hosted LLM:** Utilizes LM Studio for a private and customizable experience.
* **Browser-Based UI:** Powered by Flask for an intuitive and user-friendly interface.
* **Persistent Conversation Logs:** Automatic chat history logging and saving.

**[📚 Read the full list of features on our Wiki!](https://github.com/LumiBunny/BnuuyBotApp/wiki)**

## Getting Started 🌟

### Prerequisites:
1. [Python 3.10+](https://apps.microsoft.com/detail/9pjpw5ldxlz5?hl=en-US&gl=US)
2. [LM Studio](https://lmstudio.ai)
3. [Docker](https://docs.docker.com/desktop/setup/install/windows-install)
4. Clone the repository: `git clone https://github.com/LumiBunny/BnuuyBotApp.git`
5. Install dependencies: `pip install -r requirements.txt`
6. Run the app: `python main.py`

### My Working Setup:
As this is an app in early development, I have not used or tested it on any other hardware. Here is my current PC configuration:

+ **OS:** Windows 11
+ **GPU:** NVIDIA GeForce RTX 4060ti 16GB DDR6 VRAM (though I suspect 12GB+ would be acceptable for minimum requirements)
+ **GPU Drivers:**
   * [GeForce Game Ready Driver 580.88](https://www.nvidia.com/en-us/drivers/details/251255)
   * [CUDA Toolkit (12.8.1 or later)](https://developer.nvidia.com/cuda-downloads?target_os=Windows)
   * [NVIDIA cudNN](https://developer.nvidia.com/cudnn)
+ **RAM:** 32GB DDR5 RAM or more
+ **CPU:** Intel i9 14th gen 149000 (i7 would be acceptable too)
+ **LLM Model:** I jump around between a few, but usually a Llama 3.0-3.1 based 8B LLM model in GGUF format works well. I aim to keep the GGUF file size under 8GB so as to leave room for other LLMs and tools on my GPU

_**This project has not been tested on non-NVIDIA GPUs nor on non-Intel CPUs, so I can't guarantee stability or functionality on other confgurations at this time.**_
Performance on other systems may vary. Different tools and drivers might need to be installed and set up.

### Installation:
1. Install NVIDIA drivers and toolkits
2. Install Python 3.10 or later
3. Install LM Studio, as well as the runtime expansion packs for CUDA 12 llama.cpp (Windows) and CUDA llama.cpp (Windows)
4. Start local server in LM Studio and load LLM of choice
5. Install Docker
6. Run the (**quick start setup**)[https://github.com/travisvn/openai-edge-tts?tab=readme-ov-file#%EF%B8%8F-quick-start] for the Docker server for TTS functionality
7. run `python app.py` from within the BunnyBotApp folder

## Latest Updates 📢
**Version 0.4.4:** Overhauled the browser UI with a new and improved version to make it more visually pleasing, add control buttons and make it more user friendly, as well as some bug fixes.

**[📝Click here to read the full patch notes.](https://github.com/LumiBunny/BnuuyBotApp/wiki/1.-Patch-Notes)**

### [🏡 Visit our Wiki for full documentation!](https://github.com/LumiBunny/BnuuyBotApp/wiki)
