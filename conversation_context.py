"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
"""


import logging

try:
    from .config import SYSTEM_PROMPT
except ImportError:
    from config import SYSTEM_PROMPT

logger = logging.getLogger(__name__)
import config

import json
import os
import utils as uti 


class ConversationContext:
    def __init__(self, username=None):
        self.username = username
        self.messages = [self.assemble_system_prompt()]
        self.input_tokens = 0
        self.output_tokens = 0
    
    def track_input(self, messages):
        for message in messages:
            self.input_tokens += uti.count_tokens(str(message))
    
    def track_output(self, response):
        self.output_tokens += uti.count_tokens(response)

    def save_to_file(self, path):
        """
        Persistă conversația pe disc (memoria care supraviețuiește repornirii).

        Salvăm istoricul FĂRĂ primul mesaj (system prompt-ul), pentru că el se
        reasamblează proaspăt din knowledge/ la fiecare pornire; salvăm și
        contoarele de tokeni ca să continue acumularea, nu s-o ia de la zero.
        """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        data = {
            "messages": self.messages[1:],
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_file(self, path):
        """
        Reîncarcă o conversație salvată peste system prompt-ul proaspăt.

        Dacă fișierul nu există (prima conversație a userului) sau e corupt,
        pornim gol - fără crash (același stil de error handling ca în rest).
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except json.JSONDecodeError:
            logger.warning("Session file '%s' is corrupted - starting fresh.", path)
            return
        self.messages = [self.messages[0]] + data.get("messages", [])
        self.input_tokens = data.get("input_tokens", 0)
        self.output_tokens = data.get("output_tokens", 0)

    def assemble_system_prompt(self):
        """Construiește mesajul de system prompt din knowledge/ (always_load + prompts)."""
        prompt = SYSTEM_PROMPT
        try:
            files_to_read = os.listdir("knowledge")
        except FileNotFoundError:
            logger.warning(
                "The 'knowledge' folder does not exist - "
                "starting with an empty system prompt."
            )
            return {"role": "system", "content": prompt}

        for file_to_read in files_to_read:
            sub_files = os.listdir(os.path.join("knowledge", file_to_read))
            for sub_file in sub_files:
                if file_to_read == "facts" or file_to_read == "procedures":
                    if sub_file.endswith(".json"):
                        registry_path = os.path.join("knowledge", file_to_read, sub_file)
                        try:
                            with open(registry_path, "r", encoding="utf-8") as f:
                                facts = json.load(f)
                        except json.JSONDecodeError:
                            logger.warning("Registry '%s' is not valid JSON - skipped.", registry_path)
                            continue
                        for fact in facts:
                            if fact.get("always_load"):
                                doc_path = os.path.join("knowledge", file_to_read, fact.get("id") + '.md')
                                try:
                                    with open(doc_path, "r", encoding="utf-8") as f2:
                                        prompt += "\n\n## " + fact.get("name") + "\n" + f2.read()
                                except FileNotFoundError:
                                    logger.warning("Document '%s' is listed in the registry but does not exist - skipped.", doc_path)
                elif file_to_read == "prompts":
                    with open(os.path.join("knowledge", file_to_read, sub_file), "r", encoding="utf-8") as f:
                        prompt += "\n" + f.read()

        if self.username:
            prompt += (
                "\n\n## Current User (authoritative)\n"
                f"The person you are talking to is named: {self.username}. This is "
                "their real name for this whole session. If they ask what their name "
                f"is, answer exactly \"{self.username}\".\n"
                "IMPORTANT: a name written inside an uploaded document, CV or file is "
                "the SUBJECT of that document, NOT this user's name. Never take the "
                f"user's name from a document — it is always \"{self.username}\".\n"
                "When using tools that need a student/user name (save_student_evaluation, "
                f"get_student_record), always pass \"{self.username}\" automatically — "
                "do not ask them to state it, unless they explicitly ask about someone "
                "else's work."
            )

        return {
            "role": "system",
            "content": prompt
        }

    def add_message(self, message):
        self.messages.append(message)

    def get_history(self):
        return self.messages
    
    def compress_history(self, max_tokens, llm_client=None):
        """
        Ține istoricul conversației sub max_tokens ("smart compression").

        Strategia:
        - system prompt-ul (self.messages[0]) NU se atinge NICIODATĂ;
        - ultimele KEEP_RECENT_MESSAGES mesaje rămân intacte (modelul are
          nevoie de contextul proaspăt cuvânt cu cuvânt);
        - tot ce e între ele ("mesajele vechi") se trimite la LLM cu
          instrucțiunea "rezumă" și se înlocuiește cu UN singur mesaj-rezumat;
        - dacă llm_client e None sau rezumatul eșuează → fallback pe
          sliding window (pur și simplu arunci mesajele vechi).

        Args:
            max_tokens (int): pragul de tokeni (MAX_CONTEXT_TOKENS din config).
            llm_client: clientul LLM folosit pentru rezumat; None = fără rezumat.
        """
        # 1. Măsoară istoricul; dacă încape sub prag, nu facem nimic.
        total = sum(uti.count_tokens(str(m)) for m in self.messages)
        if total <= max_tokens:
            return

        # 2. Împarte în [system prompt] [mesaje vechi] [ultimele KEEP_RECENT].
        if len(self.messages) <= 1 + config.KEEP_RECENT_MESSAGES:
            return  # prea puține mesaje ca să avem ce comprima
        system_prompt = self.messages[0]
        recent = self.messages[-config.KEEP_RECENT_MESSAGES:]
        old = self.messages[1:-config.KEEP_RECENT_MESSAGES]

        # Un mesaj "tool" nu poate deschide fereastra recentă fără mesajul
        # "assistant" cu tool_calls dinaintea lui (altfel API-ul dă 400).
        while recent and recent[0].get("role") == "tool":
            old.append(recent.pop(0))

        # 3. Serializează mesajele vechi într-un singur text pentru rezumat.
        lines = [f"{m.get('role')}: {str(m.get('content') or '')}" for m in old]
        conversation_text = "\n".join(lines)

        # 4. Cere un rezumat de la LLM (dacă avem client).
        summary = None
        if llm_client is not None:
            response = llm_client.generate_response([
                {"role": "system", "content": (
                    "You summarize conversations. Reply ONLY with a short "
                    "factual summary (max 150 words). Keep: names, grades "
                    "given, decisions made, questions that are still open."
                )},
                {"role": "user", "content": conversation_text},
            ])
            summary = response["message"].get("content", "") or None

        # 5. Reconstruiește: cu rezumat dacă a reușit, altfel sliding window.
        if summary:
            self.messages = [
                system_prompt,
                {"role": "system",
                 "content": "Summary of the earlier conversation: " + summary},
            ] + recent
        else:
            self.messages = [system_prompt] + recent

        # ---- Verificare rapidă (șterge după ce merge) ------------------------
        #print(f"[compress] {total} tokeni -> istoric redus la "
        #        f"{len(self.messages)} mesaje")

