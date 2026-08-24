class ConversationMemory:
    def __init__(self):
        self.history = []
        
    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})
        self._trim()
        
    def add_ai_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})
        self._trim()
        
    def get_history(self):
        return self.history
        
    def clear(self):
        self.history = []
        
    def _trim(self):
        if len(self.history) > 6:
            self.history = self.history[-6:]

memory = ConversationMemory()
