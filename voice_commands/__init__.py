# voice_commands/__init__.py

# Import main classes to expose at package level
from .attention import AttentionHandler
from .commands import CommandProcessor
from .manager import VoiceCommandManager

# This allows users to do:
# from voice_commands import VoiceCommandManager
# Instead of:
# from voice_commands.manager import VoiceCommandManager