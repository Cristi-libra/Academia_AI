"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
"""


try:
    from .config import SYSTEM_PROMPT
except ImportError:
    from config import SYSTEM_PROMPT

import json
import os
import utils as uti 


class ConversationContext:
    def __init__(self):
        self.messages = [self.assemble_system_prompt()]
        self.input_tokens = 0
        self.output_tokens = 0
    
    def track_input(self, messages):
        for message in messages:
            self.input_tokens += uti.count_tokens(str(message))
    
    def track_output(self, response):
        self.output_tokens += uti.count_tokens(response)

    def assemble_system_prompt(self):
        # TODO: return a system message dict with the system prompt from config
        # Hint: Observe the message format used in agent.py
        # Hint: The system prompt should be a message dict with role "system"
        prompt = SYSTEM_PROMPT
        try:
            files_to_read = os.listdir("knowledge")
        except FileNotFoundError:
            print(
                "Warning: the 'knowledge' folder does not exist - "
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
                            print(f"Warning: registry '{registry_path}' is not valid JSON - skipped.")
                            continue
                        for fact in facts:
                            if fact.get("always_load"):
                                doc_path = os.path.join("knowledge", file_to_read, fact.get("id") + '.md')
                                try:
                                    with open(doc_path, "r", encoding="utf-8") as f2:
                                        prompt += "\n\n## " + fact.get("name") + "\n" + f2.read()
                                except FileNotFoundError:
                                    print(f"Warning: document '{doc_path}' is listed in the registry but does not exist - skipped.")
                elif file_to_read == "prompts":
                    with open(os.path.join("knowledge", file_to_read, sub_file), "r", encoding="utf-8") as f:
                        prompt += "\n" + f.read()

        return {
            "role": "system",
            "content": prompt
        }

    def add_message(self, message):
        # TODO: Implement message addition logic

        self.messages.append(message)

    def get_history(self):
        # TODO: return the full message history
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
        # ---- Pasul 1: numără tokenii istoricului actual --------------------
        # HINT: e FIX aceeași buclă ca în track_input, doar că aduni într-o
        #       variabilă locală (ex. total), NU în self.input_tokens —
        #       aia e contabilitatea de cost, asta e doar o măsurătoare.
        total = 0
        # TODO: adună count_tokens(str(m)) pentru fiecare m din self.messages

        # ---- Pasul 2: dacă încăpem, nu facem nimic --------------------------
        # HINT: early return — același pattern ca exists-check-ul din
        #       embedding_generator.
        # TODO: if total <= max_tokens: return

        # ---- Pasul 3: împarte istoricul în 3 zone ---------------------------
        #   [ system prompt ][ ...mesaje vechi... ][ ultimele KEEP_RECENT_MESSAGES ]
        # HINT: slicing pe liste:
        #       system_prompt = self.messages[0]
        #       recent        = self.messages[-KEEP_RECENT_MESSAGES:]
        #       old           = self.messages[1:-KEEP_RECENT_MESSAGES]
        #       (importă KEEP_RECENT_MESSAGES din config, sus, lângă SYSTEM_PROMPT)
        # HINT-CAPCANĂ 1: dacă istoricul are ≤ 1 + KEEP_RECENT_MESSAGES mesaje,
        #       `old` iese gol → return, nu ai ce comprima.
        # HINT-CAPCANĂ 2: primul mesaj din `recent` NU are voie să aibă
        #       role == "tool" fără mesajul assistant cu tool_calls dinaintea
        #       lui (API-ul dă eroare 400). Fix simplu: cât timp
        #       recent[0].get("role") == "tool", mută-l pe recent[0] la finalul
        #       lui `old` (adică list.pop(0) + append).
        # TODO: cele 3 variabile + cele 2 verificări

        # ---- Pasul 4: transformă mesajele vechi într-un singur text ---------
        # HINT: vrei ceva de forma:
        #           user: intrebarea lui...
        #           assistant: raspunsul lui...
        #       Construiește o listă de linii f"{rol}: {content}" și apoi
        #       "\n".join(linii) — același pattern ca relevant_text din agent.py.
        # HINT: content poate fi None la mesajele assistant cu tool_calls —
        #       folosește str(m.get("content")) ca să nu crape.
        # TODO: conversation_text = ...

        # ---- Pasul 5: cere rezumatul de la LLM -------------------------------
        # HINT: generate_response primește o LISTĂ de mesaje în formatul
        #       obișnuit. NU trimite istoricul! Construiește pe loc DOAR două:
        #         1. {"role": "system", "content": "You summarize conversations.
        #             Reply ONLY with a short factual summary (max 150 words).
        #             Keep: names, grades given, decisions made, questions that
        #             are still open."}
        #         2. {"role": "user", "content": conversation_text}
        # HINT: răspunsul se citește exact ca în agent.py:
        #       response["message"].get("content", "")
        # HINT-CAPCANĂ 3: după 2.2, generate_response nu mai aruncă excepții —
        #       la eroare ÎNTOARCE TEXTUL ERORII drept content! Dacă-l folosești
        #       orbește, îți bagi "Could not reach the model..." în istoric ca
        #       "rezumat". Deci: dacă llm_client e None SAU summary iese gol →
        #       sari direct la fallback (Pasul 7). (Perfecționism opțional: fă
        #       generate_response să întoarcă și un flag de eroare, sau verifică
        #       dacă summary începe cu un mesaj de eroare cunoscut.)
        # TODO: summary = ... (sau None dacă nu se poate)

        # ---- Pasul 6: reconstruiește istoricul (cu rezumat) ------------------
        # HINT: o singură atribuire:
        #       self.messages = [system_prompt,
        #                        {"role": "system",
        #                         "content": "Summary of the earlier "
        #                                    "conversation: " + summary}] + recent
        # TODO (doar dacă ai un summary valid)

        # ---- Pasul 7: fallback = sliding window ------------------------------
        # HINT: exact linia de la Pasul 6, dar FĂRĂ mesajul-rezumat:
        #       self.messages = [system_prompt] + recent
        # TODO (când summary e None/gol)

        # ---- Verificare rapidă (șterge după ce merge) ------------------------
        # print(f"[compress] {total} tokeni -> istoric redus la "
        #       f"{len(self.messages)} mesaje")

