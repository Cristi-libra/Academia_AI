# Ghid Lab 5 — Exercițiile 3, 4, 5 (Chunking, Embeddings, Semantic Search)

> Ghid de învățare: îți spune **ce** să faci și **cu ce unelte**, nu îți dă soluția.
> Codul îl scrii tu. 💪

---

## 0. Imaginea de ansamblu (de ce facem asta)

Construiești un pipeline **RAG** (Retrieval-Augmented Generation):

```
Documente (.md)  →  Chunking (Ex. 3)  →  Embeddings (Ex. 4)  →  Semantic Search (Ex. 5)  →  Context pentru LLM
```

Ideea: documentele cu `always_load: true` intră mereu în system prompt (asta ai făcut deja la Ex. 2 în `assemble_system_prompt`). Documentele cu `always_load: false` sunt prea mari/rare ca să le bagi mereu — așa că le spargi în bucăți, le transformi în vectori și, la fiecare întrebare, cauți **doar bucățile relevante** și le adaugi în context.

---

## 1. Biblioteci necesare

Vestea bună: **nu trebuie să instalezi nimic nou**. Totul e în standard library sau deja în proiect:

| Bibliotecă | La ce o folosești | Metode cheie |
|---|---|---|
| `json` | citit registry-urile, salvat/încărcat embeddings | `json.load(f)`, `json.dump(data, f, indent=2, ensure_ascii=False)` |
| `os` / `os.path` | parcurs directoare, verificat fișiere | `os.listdir()`, `os.path.join()`, `os.path.exists()` |
| `requests` | deja folosit în `embeddings_client.py` | `requests.post(url, json=..., headers=...)` |

💡 Alternativă mai elegantă la `os.path`: modulul `pathlib`:
```python
from pathlib import Path
# Path("knowledge") / "facts" / "registry.json"  — în loc de os.path.join înlănțuit
# path.read_text(encoding="utf-8")               — în loc de open() + read()
# path.exists(), path.glob("*.md")
```

---

## 2. Exercițiul 3 — Chunking (`document_chunker.py`)

### Cerința pe scurt
O funcție **fără argumente** care:
1. Citește registry-urile din `knowledge/facts/` și `knowledge/procedures/`
2. Încarcă **doar** documentele cu `"always_load": false` (le ignoră pe cele cu `true`)
3. Sparge fiecare document în chunk-uri de dimensiune fixă (`CHUNK_SIZE` din `config.py`)
4. Returnează o listă de dict-uri:
```json
[
  {"document_id": "support_procedure", "chunk_index": 0, "content": "..."},
  {"document_id": "support_procedure", "chunk_index": 1, "content": "..."}
]
```

### Ce ai deja bun în codul tău început
Parcurgerea registry-urilor și filtrul `if not fact.get("always_load")` sunt corecte. 👍

### Ce trebuie să schimbi
Acum faci `prompt += "\n" + f2.read()` — adică **lipești toate documentele într-un singur string**. Problema: pierzi informația *din ce document vine textul*, iar cerința îți cere `document_id` per chunk. Deci:

- În loc să acumulezi într-un string, **procesează fiecare document separat**: citește-l → sparge-l în chunk-uri → adaugă dict-urile în lista de rezultat.
- Ai deja `id`-ul documentului la îndemână: `fact.get("id")` — exact ce trebuie pentru `document_id`.

### Cum spargi textul în chunk-uri (alege o variantă)

**Varianta A — felii de caractere** (cea mai simplă):
```python
text[i : i + CHUNK_SIZE]   # cu i mergând din CHUNK_SIZE în CHUNK_SIZE
# range(start, stop, step) e prietenul tău aici
```
Dezavantaj: poate tăia un cuvânt la mijloc.

**Varianta B — pe cuvinte** (mai curată semantic, recomandată):
1. `words = text.split()` — sparge în cuvinte (slide-ul 5 din PPT!)
2. Ia câte `CHUNK_SIZE` cuvinte odată (tot cu slicing pe listă: `words[i : i + CHUNK_SIZE]`)
3. Reconstruiește textul: `" ".join(bucata_de_cuvinte)`

⚠️ Decide și fii consistent: `CHUNK_SIZE = 100` înseamnă 100 de **caractere** sau 100 de **cuvinte**? Pentru varianta B, 100 de cuvinte e o valoare rezonabilă.

### Pentru `chunk_index`
Folosește `enumerate()` când construiești dict-urile — îți dă indexul gratis, fără contor manual:
```python
for index, chunk in enumerate(lista_de_chunkuri):
    ...
```

### Cum testezi
Adaugă temporar la finalul modulului:
```python
if __name__ == "__main__":
    chunks = load_n_chunk_docs()
    print(len(chunks))       # câte chunk-uri au ieșit?
    print(chunks[0])         # arată formatul corect?
    print(chunks[-1])        # ultimul chunk conține finalul documentului?
```
Rulează cu `python document_chunker.py` din directorul `lab_5_skel`.

---

## 3. Exercițiul 4 — Generarea și salvarea embeddings (`embedding_generator.py`)

### Cerința pe scurt
Modul **nou** care:
1. Ia chunk-urile de la Ex. 3 (importă funcția ta: `from document_chunker import ...`)
2. Pentru fiecare chunk, generează un embedding cu `EmbeddingsClient.get_embedding(text)` — **există deja**, nu o rescrii
3. Salvează totul într-un JSON cu formatul:
```json
[
  {"document_id": "...", "chunk_index": 0, "content": "...", "embedding": [0.12, -0.44]}
]
```
4. **Nu regenerează** dacă fișierul există deja (hint-ul din PPT)

### Pași de gândire
- Observă că formatul cerut = dict-ul de la Ex. 3 **+ o cheie în plus** (`"embedding"`). Deci poți lua fiecare dict și doar să-i adaugi cheia: `chunk["embedding"] = ...`
- Calea fișierului JSON: pune-o ca **o constantă în `config.py`** (ex. `EMBEDDINGS_FILE = "embeddings.json"`) — Ex. 5 spune explicit că „calea fișierului este cunoscută și setată în config".
- Pentru „nu regenera dacă există": `os.path.exists(EMBEDDINGS_FILE)` la începutul funcției → dacă există, ieși devreme (early return). 
- La salvare: `json.dump(data, f, indent=2, ensure_ascii=False)` — `ensure_ascii=False` păstrează diacriticele românești lizibile.

### ⚠️ Capcane pe care le-am observat în proiectul tău
1. **`config.py` nu are `API_KEY`**, dar `embeddings_client.py` și `llm_client.py` îl importă → aplicația crapă cu `ImportError` la pornire. Trebuie să adaugi `API_KEY = "..."` în `config.py` (vezi secțiunea 6 despre Gemini și secțiunea 7 despre cum să NU-ți pui cheia în git).
2. **Endpoint-ul de embeddings** e setat pe Ollama local (`http://localhost:11434/api/embed`, model `bge-m3:latest`). Ca să meargă, trebuie să ai [Ollama](https://ollama.com) pornit și modelul tras: `ollama pull bge-m3`. Alternativa: folosește Gemini și pentru embeddings (secțiunea 6).

### Cum testezi
Rulează modulul, apoi deschide JSON-ul generat și verifică: are toate cele 4 chei? `embedding` e o listă lungă de numere (bge-m3 → 1024 de dimensiuni)? Rulează a doua oară — ar trebui să fie instant (nu regenerează).

---

## 4. Exercițiul 5 — Semantic Search (`EmbeddingsClient.semantic_search`)

### Cerința pe scurt
Completezi metoda `semantic_search(self, user_question)` din `embeddings_client.py`:
1. Încarcă JSON-ul de la Ex. 4 (calea din config)
2. Generează embedding-ul întrebării: `self.get_embedding(user_question)`
3. Pentru fiecare chunk: `self.cosine_similarity(embedding_intrebare, chunk["embedding"])` — **există deja**
4. Sortează descrescător după scor
5. Păstrează doar top-N chunk-uri care depășesc un prag minim
6. Returnează lista în formatul:
```json
[
  {"document_id": "support_procedure", "chunk_index": 3, "similarity": 0.94, "content": "..."}
]
```

### Unelte Python pentru pașii 4–5

**Sortare descrescătoare după o cheie din dict:**
```python
sorted(rezultate, key=lambda r: r["similarity"], reverse=True)
```

**Top-N:** slicing pe listă → `lista_sortata[:N]`

**Prag minim:** fie un `if` în bucla de calcul, fie o list comprehension:
```python
[r for r in rezultate if r["similarity"] >= PRAG]
```

💡 `N` (ex. 3) și `PRAG` — pune-le tot ca constante în `config.py` (ex. `TOP_N_CHUNKS`, `SIMILARITY_THRESHOLD`). Pentru prag, docstring-ul din `cosine_similarity` îți dă deja interpretarea: peste 0.7 = similar. Începe cu ceva permisiv (0.4–0.5) și ajustează după ce vezi scorurile reale.

### Cum testezi
```python
if __name__ == "__main__":
    client = EmbeddingsClient()
    print(client.semantic_search("How do I reset my password?"))
```
Pune o întrebare la care știi că răspunsul e în `support_procedure.md` și verifică dacă chunk-ul corect iese primul, cu scor mare. Apoi pune o întrebare complet nelegată („care e capitala Franței?") — scorurile ar trebui să fie mici, sub prag → listă goală.

### Bonus (din PPT): integrarea în system prompt
Ideea: în `Agent.process_message` sau în `ConversationContext`, înainte de a trimite mesajul la LLM, apelezi `semantic_search(user_message)` și adaugi conținutul chunk-urilor găsite în context (de ex. ca o secțiune „# Relevant Knowledge" adăugată la system prompt sau ca mesaj suplimentar). Gândește-te: unde e locul cel mai natural, dat fiind că `ConversationContext` construiește promptul o singură dată în `__init__`?

---

## 5. Sfaturi de cod elegant (valabile peste tot)

1. **Funcții mici, un singur rol.** În loc de o mega-funcție, sparge: una care citește registry-urile și returnează documentele de procesat, una care sparge un text în chunk-uri, una care le asamblează. Fiecare devine testabilă separat.
2. **Redu nesting-ul cu `continue`.** Codul tău actual are 5 niveluri de indentare. Compară:
   ```python
   # în loc de:
   if file_to_read == "facts" or file_to_read == "procedures":
       if sub_file.endswith(".json"):
           ...
   # poți scrie:
   if file_to_read not in ("facts", "procedures"):
       continue
   if not sub_file.endswith(".json"):
       continue
   ...
   ```
3. **Nu ghici numele fișierului de registry.** Știi că se numește `registry.json` — deschide-l direct cu `os.path.join("knowledge", categorie, "registry.json")` în loc să parcurgi toate fișierele și să filtrezi după extensie.
4. **Constante în `config.py`, nu valori hardcodate** — `CHUNK_SIZE` e deja acolo; adaugă la fel căile de fișiere, `TOP_N_CHUNKS`, `SIMILARITY_THRESHOLD`.
5. **Type hints** ca în `embeddings_client.py`: `def load_n_chunk_docs() -> list[dict]:` — documentație gratis.
6. **`with open(...)` mereu** (deja faci asta corect 👍) și mereu cu `encoding="utf-8"`.
7. **Nume descriptive**: `category` în loc de `file_to_read` (care de fapt e un director!), `doc_entry` în loc de `fact` (în procedures nu sunt „facts").

---

## 6. Conectarea la Gemini cu API key

Proiectul tău e configurat acum pentru Azure OpenAI (chat) + Ollama local (embeddings). Poți trece pe **Google Gemini**, care are un free tier generos și un endpoint **compatibil OpenAI** — adică merge cu `llm_client.py` al tău aproape fără modificări.

### Pasul 1 — Obții cheia
1. Mergi pe **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** (Google AI Studio, cont Google normal)
2. `Create API key` → copiezi cheia (arată ca `AIzaSy...`)

### Pasul 2 — Configurezi `config.py`
Gemini expune un endpoint compatibil OpenAI la:
```
https://generativelanguage.googleapis.com/v1beta/openai
```
Deci în `config.py` setezi:
```python
MODEL_NAME = "gemini-2.0-flash"          # sau alt model Gemini
MODEL_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
API_KEY = "cheia-ta"                     # mai bine din env var — vezi secțiunea 7!
```

De ce funcționează cu codul tău existent:
- `LLMClient._headers()` — ramura non-Azure pune `Authorization: Bearer <API_KEY>` → exact ce așteaptă Gemini. ✅
- `generate_response` citește răspunsul din `choices[0].message` → formatul OpenAI pe care îl întoarce și Gemini. ✅
- ⚠️ Atenție: codul tău adaugă `/chat/completions` automat **doar** dacă endpoint-ul se termină în `/openai/v1`. Endpoint-ul Gemini se termină în `/openai`, deci pune calea completă (cu `/chat/completions`) direct în config, ca mai sus.

### Pasul 3 (opțional) — Embeddings tot prin Gemini
Dacă nu vrei să rulezi Ollama local, Gemini are și embeddings pe același endpoint compatibil OpenAI:
```python
EMBEDDINGS_MODEL = "gemini-embedding-001"
EMBEDDINGS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/embeddings"
```
⚠️ Dar formatul răspunsului diferă de Ollama! `get_embedding` al tău citește `response.json()["embeddings"][0]` (format Ollama), pe când formatul OpenAI/Gemini este:
```json
{"data": [{"embedding": [0.12, ...]}]}
```
adică `response.json()["data"][0]["embedding"]`. Va trebui să adaptezi `get_embedding` să suporte ambele (hint: verifică ce chei există în răspuns, similar cu cum `generate_response` verifică `"message"` vs `"choices"`).

📌 **Important**: orice model de embeddings alegi, folosește **același model** și la generare (Ex. 4) și la căutare (Ex. 5) — vectorii din modele diferite nu sunt comparabili! Dacă schimbi modelul, șterge JSON-ul și regenerează.

### Limite free tier (orientativ)
Gemini free tier: ~10-15 requests/minut la flash. Pentru laborator e suficient, dar dacă primești `429 Too Many Requests`, așteaptă un minut.

---

## 7. Nu-ți pune API key-ul în git! 🔒

Repo-ul tău e pe GitHub. Dacă scrii `API_KEY = "AIzaSy..."` direct în `config.py` și dai commit, cheia devine publică (și boții o găsesc în minute). Varianta corectă:

```python
# în config.py:
import os
API_KEY = os.environ.get("GEMINI_API_KEY", "")
```

Și setezi variabila de mediu în PowerShell înainte să rulezi:
```powershell
$env:GEMINI_API_KEY = "cheia-ta"
python main.py
```
(sau permanent, din Windows: Settings → System → About → Advanced system settings → Environment Variables)

---

## 8. Cum extinzi Knowledge Base-ul (și ce ai greșit acolo)

### Regulile jocului (din Ex. 1, slide 11)

```
knowledge/
├── prompts/       → personalitatea agentului; TOATE fișierele se încarcă automat, FĂRĂ registry
├── facts/         → informații permanente; are registry.json
└── procedures/    → instrucțiuni operaționale; are registry.json
```

Fiecare intrare din `registry.json` are 4 proprietăți obligatorii:

| Proprietate | Regulă |
|---|---|
| `id` | **numele fișierului fără extensie** — trebuie să se potrivească EXACT, altfel codul tău face `id + ".md"` și crapă cu `FileNotFoundError` |
| `name` | titlul afișat / folosit ca titlu de secțiune în system prompt |
| `description` | o frază — ce conține documentul |
| `always_load` | `true` = intră mereu în system prompt; `false` = intră în pipeline-ul de chunking + embeddings (Ex. 3–5) |

### Pașii ca să adaugi un document nou

1. **Creezi fișierul** `.md` în directorul potrivit (`facts/` pentru informații statice, `procedures/` pentru „cum se face X")
2. **Adaugi o intrare** în `registry.json` din același director — atenție, e o **listă JSON**: virgulă după intrarea precedentă, fără virgulă după ultima (JSON-ul nu iartă trailing commas!)
3. **Alegi `always_load`**: e mic și mereu relevant (ex. date despre companie)? → `true`. E lung și relevant doar uneori (ex. handbook, proceduri)? → `false`
4. ⚠️ **Dacă e `false`: șterge fișierul de embeddings** generat la Ex. 4! Altfel logica ta „nu regenera dacă există" va folosi embeddings vechi și noul document e invizibil la căutare. (Idee de îmbunătățire: compară numărul de chunk-uri din JSON cu cel proaspăt calculat.)
5. **Verifici**: pornește agentul și pune o întrebare la care doar noul document poate răspunde.

### Ce e greșit la tine acum — concret

1. **Typo: `emplayee_handbook`** 😄 — și fișierul (`emplayee_handbook.md`), și `id`-ul din registry sunt scrise greșit (corect: `employee`). *Funcționează* pentru că cele două se potrivesc între ele, dar dacă redenumești, redenumește-le pe **amândouă simultan** — altfel `FileNotFoundError`.

2. **Ex. 2 cere titluri de secțiune, iar codul tău nu le pune.** Slide-ul 12 spune explicit: *„Pentru fiecare document inclus, utilizați proprietatea `name` ca titlu al secțiunii"* și dă structura țintă:
   ```
   # Agent Identity
   ...
   # Company Facts
   ...
   ```
   În `assemble_system_prompt` tu faci doar `prompt += "\n" + f2.read()` — lipești conținutul fără niciun titlu. Ai `fact.get("name")` la îndemână; gândește-te cum formatezi un heading markdown din el înainte de conținut. (Pentru `prompts/` nu există registry — acolo poți folosi un titlu fix sau numele fișierului.)

3. **Directoarele sunt hardcodate** — `if file_to_read == "facts" or file_to_read == "procedures"`. Merge azi, dar dacă adaugi mâine o categorie nouă (ex. `products/` cu propriul registry), o ignoră silențios. Mai robust: tratează special doar `prompts`, iar pentru orice alt subdirector caută un `registry.json` — dacă există, procesează-l la fel.

4. **Detaliu de gândire, nu bug**: `support_procedure.md` (scurt, cu pașii de password reset) e marcat `always_load: false`, deci va fi găsit doar prin semantic search. E o alegere OK pentru laborator, dar observă trade-off-ul: dacă search-ul nu-l găsește (prag prea sus, chunk tăiat prost), agentul nu știe procedura. Documentele mici și des folosite sunt candidați buni pentru `true`.

---

## 9. Checklist final

- [ ] Ex. 3: `load_n_chunk_docs()` returnează listă de dict-uri cu `document_id`, `chunk_index`, `content`
- [ ] Ex. 3: documentele cu `always_load: true` sunt ignorate
- [ ] Ex. 4: `embedding_generator.py` salvează JSON-ul și nu regenerează dacă există
- [ ] Ex. 4: `API_KEY` adăugat în `config.py` (din env var!), embeddings funcționale (Ollama sau Gemini)
- [ ] Ex. 5: `semantic_search` returnează top-N chunk-uri sortate, peste prag, cu `similarity` în rezultat
- [ ] Test: o întrebare relevantă găsește chunk-ul corect; una irelevantă returnează listă goală
- [ ] Bonus: chunk-urile relevante ajung în contextul LLM-ului
- [ ] Knowledge Base: fiecare document nou are intrare în registry cu `id` = numele fișierului; system prompt-ul folosește `name` ca titlu de secțiune (Ex. 2); embeddings regenerate după orice document nou cu `always_load: false`

Spor la treabă! 🚀
