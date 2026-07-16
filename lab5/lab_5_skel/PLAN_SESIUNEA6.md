# Plan proiect final — Sesiunea 6 (Orchestrare și Automatizare)

Estimările presupun ritmul tău actual (student + Copilot ca autocomplete). Punctajele sunt din PPT.

---

## 🗺️ Harta rapidă — ce task, ce fișier, ce funcție

| Task | Fișier principal | Ce faci acolo | Status |
|---|---|---|---|
| count_tokens cu tiktoken (oblig., Ex.1) | `utils.py` | ✅ `tiktoken.get_encoding("cl100k_base")` | ✅ |
| Token tracking (oblig., Ex.2) | `conversation_context.py` + `agent.py` + `main.py` | ✅ atribute + metode (tu) + poziția apelurilor în agent reparată (Claude); main.py curățat (tu) | ✅ |
| Constante preț (oblig., Ex.3) | `config.py` | 🟨 redenumire `MILLION` OK, dar valorile sunt încă 30/70 — cerința zice **2.0 / 10.0** (config.py:33-34) | 🟨 |
| Titluri secțiuni (oblig.) | `conversation_context.py` | ✅ heading din `name` (tu) + spațiul lipsă `## ` (Claude) | ✅ |
| 2.1 Fallback | `llm_client.py` + `agent.py` | ✅ retry (tu) + mesaje pe tip de eroare (Claude) + ramura `else:` la search (tu) | ✅ |
| 2.2 Error handling | `llm_client.py`, `embeddings_client.py`, `embedding_generator.py`, `document_chunker.py`, `conversation_context.py` | ✅ implementat + testat (fișiere lipsă/corupte, Ollama oprit, cheie invalidă, timeout) | ✅ |
| 2.3 Cost optimization | `config.py` + README | `TOP_N` 20 → 3–5; documentezi strategia | ⬜ |
| 2.4 Context recycling | `conversation_context.py` | 🟨 SCHELET scris de Claude în `compress_history` (7 pași cu TODO + hinturi) — TU completezi TODO-urile, apoi decomentezi apelul din `agent.py::process_message` | 🟨 |
| 2.5 Scalability | `README.md` (nou) | zero cod — documentezi cum se extinde | ⬜ |
| 2.6 Code quality | `agent.py`, `utils.py`, `embeddings_client.py` | o singură instanță `EmbeddingsClient` în `Agent.__init__`; fără print-uri debug | ⬜ |
| Chunk overlap (2p) | `document_chunker.py` + `config.py` | pasul buclei devine `CHUNK_SIZE - CHUNK_OVERLAP`; apoi ștergi embeddings.json | ⬜ |
| Embedding cache (2p) | `embedding_generator.py` | formalizezi exists-check-ul existent | ⬜ |
| Retrieval tuning (2p) | `config.py` + README | experimente cu threshold/top-N documentate | ⬜ |
| Dedicated models (2p) | — | doar README: bge-m3 + Gemini sunt deja separate | ⬜ |
| Sessions (2p+2p+1p) | `conversation_context.py` + `main.py` | metode noi `save_to_file`/`load_from_file`; folder `sessions/` | ⬜ |
| CLI — Calea A (4p) | doar `main.py` | `rich`: Console, Panel, status + meniu interactiv | ⬜ |
| Web — Calea B (8p) | `api.py` (nou) + `static/index.html` (nou) | FastAPI care refolosește Agent/Context; `main.py` rămâne CLI | ⬜ |
| Extra tools (3p) | `tools/` | ✅ 7 tool-uri implementate și înregistrate în `tools/tools.py` | ✅ |
| Knowledge nou | `knowledge/` | ✅ 3 facts + 4 procedures pe persona profesor, registries actualizate | ✅ |
| Identity extins | `knowledge/prompts/identity.md` | ✅ regulile 9–12 (grounding, tool discipline, evaluare, character) | ✅ |
| API key în env var | `config.py` | ✅ `os.environ.get("GEMINI_API_KEY", "")` — tu doar setezi variabila + regenerezi cheia | ✅ |

Detaliile fiecărui rând sunt mai jos, în secțiunea lui, în blocurile „📍 Unde în cod".

---

## 📓 Jurnal — cine a făcut ce și unde

**Făcute de TINE:**
- `utils.py` — count_tokens rescris cu tiktoken (cl100k_base)
- `config.py` — redenumirea `MILLION`, ștergerea globalelor `*_TOTAL`
- `conversation_context.py` — atributele + metodele `track_input`/`track_output`; heading-urile din registry `name` în `assemble_system_prompt`
- `agent.py` — ramura `else:` cu mesajul „no relevant knowledge found" (fallback 2.1)
- `llm_client.py` — bucla de retry (2 încercări) din 2.1
- `main.py` — curățat: afișează `context.input_tokens`/`output_tokens`, costuri calculate pe loc

**Făcute de CLAUDE (cu acordul tău):**
- `tools/` — 7 tool-uri noi: web_search, fetch_page, check_python_code, save_student_evaluation, get_student_record, current_datetime, search_knowledge_base + înregistrarea în `tools.py`
- `knowledge/` — înlocuit complet: 3 facts + 4 procedures pe persona profesor + registries
- `knowledge/prompts/identity.md` — regulile 9–12 (grounding, tool discipline, evaluare, character)
- `config.py` — API key din env var; constante noi (EMBEDDINGS_FILE, STUDENT_RECORDS_FILE, WEB_SEARCH_MAX_RESULTS, FETCH_PAGE_MAX_CHARS, MAX_CONTEXT_TOKENS, KEEP_RECENT_MESSAGES)
- **2.2 Error Handling complet** — `llm_client.py` (mesaje pe tip de eroare + timeout=60), `embeddings_client.py` (Ollama oprit / fișier lipsă / JSON corupt → mesaj clar + continuă fără RAG), `embedding_generator.py`, `document_chunker.py`, `conversation_context.py` (registry/documente lipsă → warning + skip); testat pe 7 scenarii
- `agent.py` — reparat pozițiile track_input/track_output (bug care crăpa la primul tool call)
- `conversation_context.py` — fix spațiu heading (`##Nume` → `## Nume`)
- `conversation_context.py::compress_history` — SCHELETUL cu 7 pași + hinturi pentru 2.4 (de completat de tine)
- `.gitignore` + scos din git index `.pyc`/`embeddings.json`; `requirements.txt`

**Reparate pe parcurs (bug-uri prinse):**
- generator în loc de string la `count_tokens` (track_input) → TypeError
- apelurile de tracking băgate ca argumente în `generate_response` → „multiple values for argument tools"
- `track_output(istoric)` în loc de `track_input` la al doilea request → TypeError la tool calls
- redenumire `MILLION` pe jumătate → AttributeError (reparată de tine după diagnostic)

---

## 0. URGENT înainte de orice push pe git

- [x] ~~Cheia API hardcodată~~ — REZOLVAT: `config.py` citește acum
  `os.environ.get("GEMINI_API_KEY", "")`.
- [x] **TU**: setează variabila de mediu înainte de rulare —
  PowerShell: `$env:GEMINI_API_KEY = "cheia-ta"` (sau permanent din System Properties).
- [x] **TU**: regenerează cheia din Google AI Studio — cea veche a fost expusă.
- [x] `.gitignore` — REZOLVAT: acoperă `venv/`, `__pycache__/`, `*.pyc`,
  `embeddings.json`, `student_records.json`, `~$*`; fișierele `.pyc` și
  `embeddings.json` comise istoric au fost scoase din git index.

**Timp rămas: ~5 min (doar cheia)**

---

## 1. Cerințe obligatorii (10p) — status actual

| Cerință | Status |
|---|---|
| Agent cu personalitate | ✅ `prompts/identity.md` ("Gem") |
| Conversation Context | ✅ |
| Dynamic System Prompt | ⚠️ merge, dar nu folosește `name` din registry ca titlu de secțiune |
| Knowledge Base (prompts/facts/procedures) | ✅ |
| Registries | ✅ |
| Chunking | ✅ `document_chunker.py` |
| Embeddings Generation | ✅ `embedding_generator.py` |
| Semantic Search | ✅ `embeddings_client.semantic_search` |
| Retrieval-based Context Injection | ✅ `agent.process_message` |
| Token Usage Tracking | ⚠️ e în `main.py` cu globale în `config`; spec-ul cere atribute în `ConversationContext`, numărând TOATE mesajele trimise → vezi Task 2 mai jos |
| Cost Estimation | 🔴 redenumire pe jumătate: `main.py:34` cere `MILLION`, config are `MILION` → crash → vezi Task 1 mai jos |

### ✅ Făcut deja
- `utils.py::count_tokens` folosește tiktoken — corect. (Polish opțional: mută
  `encoding = tiktoken.get_encoding(...)` DEASUPRA funcției, la nivel de modul —
  acum se recreează la fiecare apel, e lent degeaba. Și docstring-ul mai zice
  "word tokens" — nu mai e adevărat.)

### 🟨 Task 1: Constante preț — redenumirea e OK, mai rămân DOAR valorile (1 minut)

Redenumirea `MILLION` e făcută peste tot ✓, `main.py` folosește numele corecte ✓.
Un singur lucru rămas: în `config.py:33-34` valorile sunt încă `30` / `70`, iar
cerința Ex. 3 zice explicit `INPUT_TOKEN_PRICE_PER_MILLION = 2.0` și
`OUTPUT_TOKEN_PRICE_PER_MILLION = 10.0`. Schimbă cele două numere și gata.

### ✅ Task 2 — FĂCUT: numărătoarea de tokeni e în ConversationContext

**Cine ce a făcut**: tu — atributele + `track_input`/`track_output` în
`conversation_context.py` și curățenia din `main.py`; Claude — poziția apelurilor
în `agent.py` (track_input înainte de FIECARE din cele două `generate_response`,
track_output pe textul final înainte de `return` — la tine track_output primea
istoricul → TypeError la primul tool call). Verificat: input_tokens ≈ 1600 după
un mesaj (include system promptul). Pașii de mai jos rămân ca documentație:

**De ce**: cerința spune textual „accesați conversation_context.py și adăugați două
atribute noi: input_tokens și output_tokens". Acum numărătoarea ta e în `main.py` cu
variabile globale din `config` — funcționează, dar nu e unde cere enunțul. În plus,
tu numeri DOAR textul tastat de user, dar modelul primește la FIECARE mesaj tot
istoricul + system promptul (care la tine e uriaș — tot identity.md + course_facts).
Pe alea le plătești și nu le numeri.

**Ce înseamnă „atribut"**: o variabilă care trăiește pe obiect — orice linie de forma
`self.ceva = valoare` scrisă în `__init__`. Ai deja una: `self.messages`.

**Ce înseamnă „metodă"**: o funcție definită în interiorul clasei, cu `self` ca prim
parametru. Ai deja: `add_message`, `get_history`.

Pașii, în ordine:

1. **`conversation_context.py`, în `__init__`**, sub `self.messages = [...]`, adaugi:
   două atribute noi, `self.input_tokens` și `self.output_tokens`, ambele 0.
   (Fix ca în enunț.)

2. **Tot în clasă, prima metodă nouă** — numele tău, ex. `track_input`:
   - primește lista de mesaje care tocmai pleacă spre model;
   - pentru fiecare mesaj din listă ia `mesaj["content"]` și îl dă la `count_tokens`
     (importă funcția din `utils`);
   - adună totul la `self.input_tokens`.
   Atenție: mesajele de tool pot avea content non-string — convertește cu `str(...)`
   înainte de numărare, sau sari peste ce nu e string.

3. **A doua metodă nouă** — ex. `track_output`:
   - primește un singur string (răspunsul modelului);
   - adaugă `count_tokens(text)` la `self.output_tokens`.

4. **`agent.py::process_message`** — aici LEGI totul. Caută liniile cu
   `self.llm_client.generate_response(...)` (sunt DOUĂ: una normală + una după tool
   calls — ambele contează, ambele se plătesc!):
   - imediat ÎNAINTE de fiecare: `self.context.track_input(self.context.get_history())`
   - după ce ai răspunsul final (înainte de `return`): `self.context.track_output(...)`
     pe content-ul mesajului.

5. **`main.py`** — curățenie:
   - ștergi liniile 33-34 și 38-39 (tot ce începe cu `config.INPUT_TOKEN_TOTAL...` /
     `config.OUTPUT_...`);
   - la afișare folosești `context.input_tokens` și `context.output_tokens`
     (obiectul `context` există deja în `main()`, linia 19);
   - costul îl calculezi pe loc la afișare:
     `context.input_tokens / 1_000_000 * config.INPUT_TOKEN_PRICE_PER_MILLION`
     (+ perechea pentru output — formula din PPT).

6. **`config.py`** — ștergi cele 4 linii rămase fără rost:
   `INPUT_TOKEN_TOTAL`, `INPUT_TOKEN_TOTAL_PRICE`, `OUTPUT_TOKEN_TOTAL`,
   `OUTPUT_TOKEN_TOTAL_PRICE`.

**Test**: după primul mesaj, input_tokens trebuie să fie MULT mai mare decât ce
tastezi tu (mii de tokeni, pentru că include system promptul) — dacă vezi doar
10-20, înseamnă că numeri tot doar inputul userului.

### ✅ Task 3 — FĂCUT: titluri de secțiune în system prompt

**Cine ce a făcut**: tu — heading-ul din `fact.get("name")`; Claude — spațiul care
lipsea (`"##" + name` dădea `##Course Facts`, invalid ca heading markdown; acum e
`\n\n## Course Facts\n`, verificat cu test). Descrierea de mai jos rămâne ca documentație:

**De ce**: uită-te în `conversation_context.py::assemble_system_prompt` la linia cu
`prompt += "\n" + f2.read()`. Asta lipește conținutul documentelor always_load unul
după altul, fără nicio separare — modelul primește un text amestecat și nu știe unde
se termină un document și începe altul. Registry-ul are câmpul `"name"` (ex. "Course
Facts") care există EXACT pentru asta.

**Ce faci, exact**: e o singură linie de modificat. În acea linie, în loc să lipești
doar conținutul, lipești întâi un titlu markdown construit din `fact.get("name")`,
apoi conținutul. Forma finală a stringului adăugat trebuie să arate cam așa:

```
(linie goală)
## Course Facts
(conținutul fișierului)
```

**Test**: adaugă temporar `print(prompt)` înainte de `return` și pornește aplicația —
system promptul trebuie să aibă acum capitole vizibile `## Course Facts` etc. Șterge
print-ul după.

**Timp total secțiunea 1 rămasă: ~1 oră**

---

## 2. Required Extensions (12p) — de făcut TOATE, sunt câte 2p fiecare

Ordinea recomandată = de la ușor la greu.

### ✅ 2.1 Fallback Strategy (2p) — FĂCUT (retry: tu; mesaje de eroare: Claude; ramura else: tu)
- Când `semantic_search` întoarce listă goală → mesaj de sistem gen „nu am găsit
  informații relevante, răspunde din cunoștințe generale și spune userului asta".
- Când LLM-ul dă eroare (ai văzut deja 503 de la Gemini!) → retry o dată, apoi
  răspuns politicos de indisponibilitate în loc de traceback.
- Parțial ai deja cazul „0 chunks" — trebuie doar tratat explicit.

> 📍 **Unde în cod**
> - `llm_client.py::generate_response` — aici trăiește request-ul HTTP: try/except pe
>   `requests.post`, la 503/timeout un retry; dacă pică și a doua oară returnezi un dict
>   în ACELAȘI format (`{"message": {"content": "...indisponibil..."}}`), nu ridici excepția.
> - `agent.py::process_message` — ramura `else:` la `if semantic_search_results:` care
>   există deja: injectezi system message „nimic relevant găsit — răspunde din cunoștințe
>   generale și menționează asta".

### ✅ 2.2 Robust Error Handling (2p) — FĂCUT de Claude, testat pe 7 scenarii
- `try/except` pe toate `requests.post` (LLM + embeddings): `Timeout`,
  `ConnectionError` (Ollama oprit!), `HTTPError` cu mesaje clare.
- Fișiere lipsă: `embeddings.json`, registry-uri, documente din knowledge —
  `FileNotFoundError` cu mesaj util, nu crash.
- JSON corupt: `json.JSONDecodeError`.
- Testează concret: oprește Ollama și pornește chatbotul — ce se întâmplă?

> 📍 **Unde în cod**
> - `llm_client.py::generate_response` — `requests.exceptions.Timeout` / `ConnectionError` /
>   `HTTPError`, fiecare cu mesaj distinct.
> - `embeddings_client.py::get_embedding` — ConnectionError = „Ollama nu rulează, pornește-l";
>   `semantic_search` — `FileNotFoundError` (embeddings.json lipsă) + `json.JSONDecodeError`.
> - `conversation_context.py::assemble_system_prompt` și `document_chunker.py::load_n_chunk_docs`
>   — FileNotFoundError pe registry/documente, cu numele fișierului lipsă în mesaj.
> - Tool-urile din `tools/` au deja try/except — doar menționezi în README.

### 2.3 Cost Optimization (2p) — ~1–2h
- Mare parte există deja: `always_load`, top-N, threshold. Documentează asta!
- Adaugă: nu injecta system message cu chunks dacă nu există rezultate (ai deja),
  limitează istoricul trimis, ține `TOP_N` mic (20 e mult — 3–5 e tipic).
- Un mic raport: „prompt final = X tokeni în loc de Y (toată KB)".

> 📍 **Unde în cod**
> - `config.py` — `TOP_N` din 20 → 3–5.
> - `agent.py::process_message` — deja nu injectează system message când nu-s rezultate ✓;
>   opțional limitezi câte mesaje de istoric trimiți spre model.
> - README — paragraf care explică strategia always_load + retrieval (documentarea contează).

### 🟨 2.4 Context Recycling / Compression (2p) — SCHELET GATA, tu completezi TODO-urile (~1–2h)

**Starea**: `compress_history(max_tokens, llm_client=None)` din `conversation_context.py`
are scheletul complet scris de Claude — 7 pași comentați, cu hinturi și 3 capcane
semnalate. `config.py` are `MAX_CONTEXT_TOKENS = 6000` și `KEEP_RECENT_MESSAGES = 4`.
Apelul e pus COMENTAT la începutul lui `agent.py::process_message` — îl decomentezi
când scheletul e completat. Test: pune temporar `MAX_CONTEXT_TOKENS = 2500`, vorbește
3–4 mesaje, spune-i ceva la început („mă cheamă X") și verifică după compresie că mai știe.
- În `ConversationContext`: dacă totalul de tokeni al istoricului depășește un
  prag (`MAX_CONTEXT_TOKENS` în config), fie:
  - **varianta simplă**: păstrezi system prompt + ultimele N mesaje (sliding window);
  - **varianta smart**: trimiți mesajele vechi la LLM cu „rezumă conversația" și
    înlocuiești cu rezumatul (compression reală).
- Recomand: fă întâi sliding window, apoi upgrade la rezumat dacă ai timp.

> 📍 **Unde în cod**
> - `conversation_context.py::compress_history(max_tokens)` — **stub-ul EXISTĂ deja, gol,
>   la finalul clasei!** Aici implementezi sliding window: păstrezi `messages[0]` (system
>   prompt), elimini cele mai vechi mesaje non-system până când suma `count_tokens` pe
>   content-uri ≤ max_tokens.
> - `config.py` — constantă nouă `MAX_CONTEXT_TOKENS`.
> - Apelul: în `agent.py::process_message` imediat înainte de `generate_response`, SAU la
>   finalul lui `ConversationContext.add_message` (auto-compresie la fiecare adăugare).
> - Upgrade (compression reală): metodă nouă în `conversation_context.py` care primește
>   `llm_client`, trimite mesajele vechi cu instrucțiunea „rezumă conversația" și le
>   înlocuiește cu rezumatul.

### 2.5 Scalability & Extensibility (2p) — ~2h
- E despre arhitectură, nu funcționalități: tool-urile se adaugă doar cu un fișier
  nou în `tools/` + înregistrare; facts/procedures doar cu fișier + intrare în
  registry, fără să atingi codul. Deja stai bine — curăță și scrie un README
  care explică „cum adaugi un tool / un document" în 3 pași.

> 📍 **Unde în cod**
> - Fără funcții noi — arhitectura există deja. Livrabilul e `README.md` nou în
>   `lab_5_skel/` cu secțiunile: „Cum adaugi un tool" (fișier nou în `tools/` după
>   șablonul `lucky_number_tool.py` + o linie în `tools/tools.py`) și „Cum adaugi un
>   document" (fișier .md + intrare în `registry.json`, zero cod modificat).

### 2.6 Code Quality (2p) — ~2h (pass final)
- Constante hardcodate → config (ex. `"embeddings.json"` apare în 2 fișiere!).
- O singură instanță `EmbeddingsClient` creată în `Agent.__init__`, nu la fiecare mesaj.
- Docstrings, type hints consistente, nume clare, fără print-uri de debug.
- Fă asta ULTIMUL, ca un code review pe tine însuți.

> 📍 **Unde în cod**
> - `agent.py::__init__` — creezi `self.embeddings_client = EmbeddingsClient()` O SINGURĂ
>   dată; `process_message` folosește instanța (acum se creează la fiecare mesaj).
> - `utils.py::count_tokens` — elimini cele 3 print-uri de debug (rulează la FIECARE mesaj).
> - `embeddings_client.py::semantic_search` — print-ul „Found X chunks" devine opțional.
> - Verificare valori hardcodate: caută prin cod "embeddings.json", "0.5", "100" — toate
>   trebuie să vină din `config.py`.

**Timp total secțiunea 2: ~11–15 ore (≈ 2 zile de lucru)**

---

## 3. Optional Enhancements — ce recomand să alegi

### 🎁 Aproape gratis (le ai deja sau aproape) — ~2–3h pentru 6–8p
| Enhancement | Puncte | Timp | De ce |
|---|---|---|---|
| Dedicated Embedding + Chat Model | 2p | ~0h | **AI DEJA**: bge-m3 (Ollama) pentru embeddings + Gemini pentru chat. Doar documentează în README |
| Embedding Cache | 2p | ~1h | Ai deja exists-check în `embedding_generator`; formalizează (regenerare la `--reindex` sau când se schimbă docurile) |
| Retrieval Thresholds & Tuning | 2p | ~1h | Ai threshold + top-N; adaugă în README un mic experiment: ce scoruri dau întrebări relevante vs. irelevante (ai văzut 0.51–0.66) |
| Chunk Overlap Strategy | 2p | ~1–2h | Motivația ai văzut-o LIVE: propoziția cu laptopurile SE tăiată între chunk 1 și 2! Parametru `CHUNK_OVERLAP` în config, pasul buclei devine `CHUNK_SIZE - CHUNK_OVERLAP` |

> 📍 **Unde în cod (cele 4 de mai sus)**
> - **Chunk Overlap** → `document_chunker.py::load_n_chunk_docs`: pasul buclei
>   `range(0, len(words), CHUNK_SIZE)` devine `CHUNK_SIZE - CHUNK_OVERLAP`; constantă nouă
>   `CHUNK_OVERLAP` în `config.py`. ATENȚIE: după schimbare ștergi `embeddings.json` ca să
>   se regenereze cu chunk-urile noi.
> - **Embedding Cache** → `embedding_generator.py::embedding_generator`: exists-check-ul
>   actual E cache-ul; formalizezi cu un parametru `force=False` sau regenerare automată
>   când documentele s-au schimbat (compari `os.path.getmtime` pe knowledge/ vs. embeddings.json).
> - **Retrieval Thresholds & Tuning** → `config.py` (ai deja `SIMILARITY_THRESHOLD`, `TOP_N`)
>   + secțiune în README cu experimentele tale (scoruri observate: relevant 0.51–0.66).
> - **Dedicated Models** → nimic de codat: bge-m3 (Ollama) + Gemini sunt deja separate în
>   `config.py`; documentezi în README.

### 🖥️ Interfață — ALEGE O SINGURĂ CALE
**Calea A — CLI îmbunătățit (4p, ~3–4h)** ← recomandat dacă timpul e scurt
- Improved CLI (1p) + Colored Terminal UI (1p): biblioteca `rich` face ambele
  în ~1h (culori, panouri, spinner cât „gândește" agentul).
- Interactive Menu System (2p): meniu la pornire (conversație nouă / continuă /
  reindexează / ieși) — se leagă frumos cu Session Management de mai jos.

> 📍 **Unde în cod (Calea A)**
> - Totul în `main.py`: `rich.console.Console` + `Panel` pentru răspunsuri,
>   `console.status("Gem se gândește...")` în jurul lui `agent.process_message`,
>   iar meniul = un `while` cu opțiuni înaintea buclei de chat din `main()`.

**Calea B — Web (8p, ~1,5–2 zile)** ← recomandat dacă vrei punctaj maxim
- HTTP Backend Service (3p) + REST API Endpoints (2p): FastAPI cu
  `POST /chat`, `GET /history`, `POST /reset` — agentul tău devine serviciu.
- Minimal Web UI (3p): o pagină HTML + fetch către API. Nu trebuie framework.
- Bonus: deschide ușa spre Multi-user Support (3p, +2–3h) dacă vrei și mai mult.

> 📍 **Unde în cod (Calea B)**
> - Fișier NOU `api.py` (FastAPI) care REFOLOSEȘTE exact construcția din `main.py::main`:
>   `LLMClient` + `ConversationContext` + `Agent(llm_client, context, tools)`; endpoints
>   `POST /chat` (primește mesajul, întoarce `agent.process_message(...)`), `GET /history`
>   (întoarce `context.get_history()`), `POST /reset`.
> - UI = folder `static/` cu un `index.html` (fetch către `/chat`); FastAPI îl servește cu
>   `StaticFiles`. `main.py` rămâne neatins, ca CLI alternativ.
> - Pentru Multi-user: un dict `{user_id: ConversationContext}` în `api.py`.

### 💾 Persistence & Sessions — merge cu ambele căi (~3–4h pentru 5p)
- Session Management (2p): salvezi istoricul în JSON la exit, îl reîncarci la pornire (~1,5h).
- Multiple Conversations per User (2p): un fișier per conversație + listare/alegere (~1,5h).
- Export/Import (1p): practic gratis după primele două (~30 min).

> 📍 **Unde în cod (Sessions)**
> - Metode NOI în `conversation_context.py`: `save_to_file(path)` / `load_from_file(path)`
>   — `json.dump`/`json.load` pe `self.messages` (la load NU dublezi system prompt-ul:
>   încarci doar mesajele user/assistant peste cel proaspăt asamblat).
> - Apelate din `main.py`: save la `exit`, load la pornire.
> - Multiple conversations = folder `sessions/` cu un fișier JSON per conversație +
>   listare/alegere în meniul din `main.py::main`. Export/Import = aceleași două metode
>   cu o cale aleasă de user.

### 🔧 AI Features — câștig ușor
- Extra Tools (1p/tool, max 3p): ✅ **FĂCUT** — 7 tool-uri noi există deja în `tools/`
  (web_search, fetch_page, check_python_code, save/get_student_record, current_datetime,
  search_knowledge_base), toate înregistrate în `tools/tools.py`.

### 📊 Observability (dacă mai rămâne timp, ~2–3h pentru 4p)
- Structured Logging (2p): modulul `logging` cu format JSON — fiecare request,
  câte chunks găsite, câți tokeni (~1–1,5h).
- Performance Metrics (2p): timpi de răspuns LLM/embeddings, măsurați cu
  `time.perf_counter()`, afișați la exit (~1h).

### ❌ Ce NU recomand (efort mare / punctaj mic pentru timpul tău)
- Dynamic Tool Discovery (3p), Parallel Tool Execution (3p) — complexe, câștig mic.
- Multi-step Tool Reasoning (4p) — interesant (buclă de tool calls în loc de un
  singur pas), dar fă-l doar dacă termini tot restul (~2–3h).
- Automatic Model Selection (4p) / Multiple Models (4p) — cer infrastructură în plus.
- Incremental Re-indexing (3p) — face sens doar după Embedding Cache; ~2–3h dacă vrei.
- Prompt/Token Analytics Dashboard (3p) — doar dacă alegi Calea B (web).

---

## 4. Buget de timp total (scenarii)

| Scenariu | Conținut | Punctaj estimat | Timp |
|---|---|---|---|
| **Minim solid** | Fix-uri obligatorii + toate cele 6 extensii required | 10p + 12p = 22p | ~2 zile |
| **Recomandat** | + „aproape gratis" (8p) + Calea A CLI (4p) + Sessions (5p) + 3 tools (3p) | ~40p | ~4 zile |
| **Maxim rezonabil** | + Calea B web în loc de A (+4p) + Observability (4p) | ~48p | ~6 zile |

## 5. Ordinea de lucru recomandată

1. Securitate git (secțiunea 0) — 15 min
2. Aliniere cerințe obligatorii (secțiunea 1) — 1–2h
3. Required extensions în ordinea 2.1 → 2.6 — 2 zile
4. „Aproape gratis" — 2–3h
5. Alege calea de interfață + Sessions
6. Tools extra + Observability dacă rămâne timp
7. Code Quality pass FINAL peste tot + README

*Regula de aur: commit după fiecare punct bifat, nu la final.*
