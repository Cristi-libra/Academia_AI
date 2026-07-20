# Plan proiect final — Sesiunea 6 (Orchestrare și Automatizare)

Estimările presupun ritmul tău actual (student + Copilot ca autocomplete). Punctajele sunt din PPT.

> **Schimbare majoră față de versiunea anterioară a planului**: proiectul a migrat de pe
> Gemini pe **Azure AI Foundry / Azure OpenAI** (`gpt-5-mini`, cheie în env var
> `CHATGPT_API_KEY`), iar embeddings-urile pe **qwen3-embedding** (Ollama, local).
> Orice mențiune veche de „Gemini" / „bge-m3" din notițe se citește acum așa.
>
> **Decizie interfață (ACTUALIZAT)**: renunțăm la OpenWebUI. Am reconstruit de la zero o
> **interfață web proprie** (Claude), cu backend FastAPI (`api.py`) + `static/`:
> streaming SSE cu efect de typing, loader animat (spinner de puncte + cuvinte random),
> upload de documente (PDF/DOCX/text, citite de `document_reader.py`), memorie per user
> (`sessions/`), multi-user, temă light/dark, thinking best-effort. CLI-ul (`main.py`)
> rămâne neatins, în paralel.
>
> **`PLAN_IMPLEMENTARE_SONNET.md` a fost ȘTERS** (stack greșit + propunea OpenWebUI,
> acum irelevant).

---

## 🗺️ Harta rapidă — ce task, ce fișier, ce funcție

| Task | Fișier principal | Ce faci acolo | Status |
|---|---|---|---|
| count_tokens cu tiktoken (oblig., Ex.1) | `utils.py` | ✅ `tiktoken.get_encoding("cl100k_base")` | ✅ |
| Token tracking (oblig., Ex.2) | `conversation_context.py` + `agent.py` + `main.py` | ✅ atribute + metode (tu) + poziția apelurilor în agent reparată (Claude); main.py curățat (tu) | ✅ |
| Constante preț (oblig., Ex.3) | `config.py` | 🟨 nume corecte, dar valorile sunt încă **30/70** — cerința zice **2.0 / 10.0** (config.py:34-35) | 🟨 |
| Titluri secțiuni (oblig.) | `conversation_context.py` | ✅ heading din `name` (tu) + spațiul lipsă `## ` (Claude) | ✅ |
| Migrare Azure OpenAI | `config.py` + `llm_client.py` + `embeddings_client.py` | ✅ endpoint Azure + `_headers()` (api-key vs Bearer), model `gpt-5-mini`, embeddings `qwen3-embedding` | ✅ |
| 2.1 Fallback | `llm_client.py` + `agent.py` | ✅ retry (tu) + mesaje pe tip de eroare (Claude) + ramura `else:` la search (tu) | ✅ |
| 2.2 Error handling | `llm_client.py`, `embeddings_client.py`, `embedding_generator.py`, `document_chunker.py`, `conversation_context.py` | ✅ implementat + testat (fișiere lipsă/corupte, Ollama oprit, cheie invalidă, timeout) | ✅ |
| 2.3 Cost optimization | `config.py` + README | ✅ `TOP_N = 4` + strategia documentată în README (Claude) | ✅ |
| 2.4 Context recycling | `conversation_context.py` + `agent.py` | ✅ completat (tu) + cele 3 bug-uri reparate + schela HINT/TODO curățată (Claude) | ✅ |
| 2.5 Scalability | `README.md` (nou) | ✅ „How to add a tool / a document" (Claude) | ✅ |
| 2.6 Code quality | `agent.py`, `utils.py`, `embeddings_client.py`, `conversation_context.py` | ✅ o singură instanță `EmbeddingsClient`, encoding tiktoken la nivel de modul, print debug sub `config.DEBUG`, TODO-uri stale șterse (Claude) | ✅ |
| Chunk overlap (2p) | `document_chunker.py` + `config.py` | ✅ `CHUNK_OVERLAP = 20`, pasul buclei e `CHUNK_SIZE - CHUNK_OVERLAP` | ✅ |
| Embedding cache (2p) | `embedding_generator.py` | ✅ exists-check + `_knowledge_mtime()` recursiv (bug-ul de subfoldere reparat de Claude) | ✅ |
| Retrieval tuning (2p) | `config.py` + README | ✅ metodă + tabel în README (numerele exacte le rulezi tu) | ✅ |
| Dedicated models (2p) | README | ✅ documentat: qwen3-embedding (Ollama) + gpt-5-mini (Azure) | ✅ |
| Sessions / Memorie (2p+2p+1p) | `conversation_context.py` + `api.py` | ✅ `save_to_file`/`load_from_file` + `sessions/<user>.json` per user (Claude) | ✅ |
| **Backend web (3p+2p)** | `api.py` (nou) | ✅ FastAPI: `/chat` streaming SSE, `/upload`, `/reset`, `/history`, servește `static/` (Claude) | ✅ |
| **Multi-user Support (3p)** | `api.py` | ✅ dict `{user: Agent}`, sesiune izolată per nume, persistată pe disc (Claude) | ✅ |
| **Interfață web proprie (3p)** | `static/` (nou) | ✅ UI cu animații, streaming, loader cu puncte+cuvinte random, temă, thinking (Claude) | ✅ |
| **Upload & citire documente (1p)** | `document_reader.py` (nou) + `api.py` | ✅ PDF/DOCX/text → injectat în context, Gem le evaluează (Claude) | ✅ |
| Extra tools (3p) | `tools/` | ✅ 7 tool-uri implementate și înregistrate în `tools/tools.py` | ✅ |
| Knowledge nou | `knowledge/` | ✅ 3 facts + 4 procedures pe persona profesor, registries actualizate | ✅ |
| Identity extins | `knowledge/prompts/identity.md` | ✅ regulile 9–12 + secțiunea Persona/Gender | ✅ |
| API key în env var | `config.py` | ✅ `os.environ.get("CHATGPT_API_KEY", "")` | ✅ |

Detaliile fiecărui rând sunt mai jos, în secțiunea lui, în blocurile „📍 Unde în cod".

---

## 🐛 Bug-uri deschise (găsite la review-ul din 17 iulie)

Astea sunt în cod ACUM și trebuie reparate (sunt primele în planul pentru Sonnet):

1. **`compress_history` Pasul 4** (`conversation_context.py:156-162`) — cel mai serios:
   `conversation_text = "\n".join(f"...")` e ÎN buclă și primește un STRING, nu o listă
   → `join` intercalează `\n` între FIECARE CARACTER, iar atribuirea suprascrie la
   fiecare iterație → LLM-ul primește la rezumat doar ULTIMUL mesaj vechi, mutilat
   (câte o literă pe linie). Fix: construiește o LISTĂ de linii în buclă, `join` o
   singură dată DUPĂ buclă.
2. **`compress_history` Pasul 5** — capcana 3 din hinturi a rămas netratată: după 2.2,
   `generate_response` întoarce TEXTUL ERORII drept content la eșec. Verificarea
   actuală prinde doar string gol, deci un „Could not reach the model..." ar fi băgat
   în istoric ca „rezumat". Fix: detectează mesajele de eroare cunoscute → fallback
   sliding window.
3. **`compress_history` Pasul 3** (`conversation_context.py:143`) — hint-capcana 2 cerea
   `while`, e implementat cu `if`: dacă `recent` începe cu DOUĂ mesaje `tool`
   consecutive (tool call multiplu), API-ul tot dă 400.
4. **`compress_history` Pasul 4** — `str(m.get('content') or None)`: un content gol
   (`""`) devine literalmente string-ul `"None"`. Folosește `str(m.get("content") or "")`.
5. **Embedding cache** (`embedding_generator.py:9`) — `os.path.getmtime("knowledge")` se
   schimbă doar când se modifică COPIII DIRECȚI ai folderului; editarea unui fișier din
   `knowledge/facts/` NU atinge mtime-ul lui `knowledge/` → cache-ul nu se invalidează
   niciodată la editări de documente. Fix: max de mtime peste toate fișierele cu `os.walk`.
6. **Prețuri** (`config.py:34-35`) — încă 30/70, cerința Ex.3 zice 2.0/10.0 (vezi Task 1).
7. Cosmetic: comentariul stale din `agent.py:38-40` („decomentează linia de mai jos" —
   linia E decomentată); docstring-ul din `utils.py::count_tokens` încă zice „word tokens".

---

## 📓 Jurnal — cine a făcut ce și unde

**Făcute de TINE:**
- `utils.py` — count_tokens rescris cu tiktoken (cl100k_base)
- `config.py` — redenumirea `MILLION`, ștergerea globalelor `*_TOTAL`
- `conversation_context.py` — atributele + metodele `track_input`/`track_output`; heading-urile din registry `name` în `assemble_system_prompt`
- `agent.py` — ramura `else:` cu mesajul „no relevant knowledge found" (fallback 2.1)
- `llm_client.py` — bucla de retry (2 încercări) din 2.1
- `main.py` — curățat: afișează `context.input_tokens`/`output_tokens`, costuri calculate pe loc
- **`conversation_context.py::compress_history`** — TODO-urile din schelet completate
  (pașii 1–7); apelul decomentat în `agent.py::process_message` (mai rămân bug-urile 1–4 de sus)
- **Migrarea pe Azure OpenAI** — `config.py` (MODEL_NAME=`gpt-5-mini`, endpoint Azure AI
  Foundry, cheia din `CHATGPT_API_KEY`, embeddings `qwen3-embedding:latest`),
  `llm_client.py::_headers` + `embeddings_client.py::_headers` (api-key pt. azure.com,
  Bearer altfel)
- **Chunk overlap** — `CHUNK_OVERLAP = 20` în config + pasul buclei din
  `document_chunker.py` schimbat în `CHUNK_SIZE - CHUNK_OVERLAP`
- **Embedding cache** — exists-check + comparația `getmtime(knowledge)` vs
  `getmtime(embeddings.json)` în `embedding_generator.py` (mai rămâne bug-ul 5 de sus)
- `knowledge/prompts/identity.md` — secțiunea Persona (gen, stil de comunicare, ton)

**Făcute de CLAUDE (cu acordul tău):**
- `tools/` — 7 tool-uri noi: web_search, fetch_page, check_python_code, save_student_evaluation, get_student_record, current_datetime, search_knowledge_base + înregistrarea în `tools.py`
- `knowledge/` — înlocuit complet: 3 facts + 4 procedures pe persona profesor + registries
- `knowledge/prompts/identity.md` — regulile 9–12 (grounding, tool discipline, evaluare, character)
- `config.py` — API key din env var; constante noi (EMBEDDINGS_FILE, STUDENT_RECORDS_FILE, WEB_SEARCH_MAX_RESULTS, FETCH_PAGE_MAX_CHARS, MAX_CONTEXT_TOKENS, KEEP_RECENT_MESSAGES)
- **2.2 Error Handling complet** — `llm_client.py` (mesaje pe tip de eroare + timeout=60), `embeddings_client.py` (Ollama oprit / fișier lipsă / JSON corupt → mesaj clar + continuă fără RAG), `embedding_generator.py`, `document_chunker.py`, `conversation_context.py` (registry/documente lipsă → warning + skip); testat pe 7 scenarii
- `agent.py` — reparat pozițiile track_input/track_output (bug care crăpa la primul tool call)
- `conversation_context.py` — fix spațiu heading (`##Nume` → `## Nume`)
- `conversation_context.py::compress_history` — SCHELETUL cu 7 pași + hinturi pentru 2.4
- `.gitignore` + scos din git index `.pyc`/`embeddings.json`; `requirements.txt`

**Reparate pe parcurs (bug-uri prinse):**
- generator în loc de string la `count_tokens` (track_input) → TypeError
- apelurile de tracking băgate ca argumente în `generate_response` → „multiple values for argument tools"
- `track_output(istoric)` în loc de `track_input` la al doilea request → TypeError la tool calls
- redenumire `MILLION` pe jumătate → AttributeError (reparată de tine după diagnostic)

---

## 0. URGENT înainte de orice push pe git

- [x] ~~Cheia API hardcodată~~ — REZOLVAT: `config.py` citește acum
  `os.environ.get("CHATGPT_API_KEY", "")`.
- [x] **TU**: setează variabila de mediu înainte de rulare —
  PowerShell: `$env:CHATGPT_API_KEY = "cheia-ta"` (sau permanent din System Properties).
- [x] `.gitignore` — REZOLVAT: acoperă `venv/`, `__pycache__/`, `*.pyc`,
  `embeddings.json`, `student_records.json`, `~$*`; fișierele `.pyc` și
  `embeddings.json` comise istoric au fost scoase din git index.

---

## 1. Cerințe obligatorii (10p) — status actual

| Cerință | Status |
|---|---|
| Agent cu personalitate | ✅ `prompts/identity.md` ("Gem") |
| Conversation Context | ✅ |
| Dynamic System Prompt | ✅ heading-uri `## Name` din registry |
| Knowledge Base (prompts/facts/procedures) | ✅ |
| Registries | ✅ |
| Chunking | ✅ `document_chunker.py` (acum cu overlap) |
| Embeddings Generation | ✅ `embedding_generator.py` (acum cu cache) |
| Semantic Search | ✅ `embeddings_client.semantic_search` |
| Retrieval-based Context Injection | ✅ `agent.process_message` |
| Token Usage Tracking | ✅ atribute + track_input/track_output în `ConversationContext` |
| Cost Estimation | 🟨 formula e OK în `main.py`, dar valorile constantelor sunt greșite (Task 1) |

### 🟨 Task 1: Constante preț — mai rămân DOAR valorile (1 minut)

Redenumirea `MILLION` e făcută peste tot ✓, `main.py` folosește numele corecte ✓.
Un singur lucru rămas: în `config.py:34-35` valorile sunt încă `30` / `70`, iar
cerința Ex. 3 zice explicit `INPUT_TOKEN_PRICE_PER_MILLION = 2.0` și
`OUTPUT_TOKEN_PRICE_PER_MILLION = 10.0`. Schimbă cele două numere și gata.

### ✅ Task 2 — FĂCUT: numărătoarea de tokeni e în ConversationContext

Atributele + `track_input`/`track_output` în `conversation_context.py` (tu); poziția
apelurilor în `agent.py` (Claude — track_input înainte de FIECARE din cele două
`generate_response`, track_output pe textul final). Verificat: input_tokens ≈ 1600
după un mesaj (include system promptul).

### ✅ Task 3 — FĂCUT: titluri de secțiune în system prompt

Heading din `fact.get("name")` (tu) + spațiul lipsă după `##` (Claude). Verificat:
system promptul are capitole `## Course Facts` etc.

**Timp rămas secțiunea 1: ~1 minut (două numere în config)**

---

## 2. Required Extensions (12p) — de făcut TOATE, sunt câte 2p fiecare

### ✅ 2.1 Fallback Strategy (2p) — FĂCUT (retry: tu; mesaje de eroare: Claude; ramura else: tu)
- `llm_client.py::generate_response` — try/except pe `requests.post`, retry o dată la
  503/timeout; la eșec definitiv întoarce un dict în ACELAȘI format cu mesaj politicos.
- `agent.py::process_message` — ramura `else:` injectează „no relevant knowledge found,
  răspunde din cunoștințe generale".

### ✅ 2.2 Robust Error Handling (2p) — FĂCUT de Claude, testat pe 7 scenarii
- `llm_client.py` — Timeout / ConnectionError / HTTPError (401/403, 429, 5xx), fiecare
  cu mesaj distinct; nu mai ridică excepții spre user.
- `embeddings_client.py` — Ollama oprit / embeddings.json lipsă / JSON corupt → mesaj
  clar + continuă fără RAG.
- `conversation_context.py` + `document_chunker.py` — registry/documente lipsă →
  warning + skip.

### 2.3 Cost Optimization (2p) — ~1h
- Mare parte există deja: `always_load`, top-N, threshold, iar acum și compresia de
  context (2.4). Documentează asta!
- `TOP_N` e ÎNCĂ 20 în `config.py:26` — adu-l la 3–5.
- Un mic raport în README: „prompt final = X tokeni în loc de Y (toată KB)".

> 📍 **Unde în cod**
> - `config.py` — `TOP_N` din 20 → 3–5.
> - README — paragraf care explică strategia always_load + retrieval + compression.

### 🟨 2.4 Context Recycling / Compression (2p) — IMPLEMENTAT, mai rămân bug-urile

**Starea**: TU ai completat toți cei 7 pași din schelet (numărare tokeni, early return,
împărțirea în 3 zone, rezumat prin LLM cu fallback pe sliding window) și ai decomentat
apelul din `agent.py::process_message`. `config.py` are `MAX_CONTEXT_TOKENS = 4096` și
`KEEP_RECENT_MESSAGES = 4`.

**Ce mai trebuie**: bug-urile 1–4 din secțiunea „Bug-uri deschise" (cel mai important:
Pasul 4 — textul trimis la rezumat e stricat). După fix, testul: pune temporar
`MAX_CONTEXT_TOKENS = 2500`, vorbește 3–4 mesaje, spune-i ceva la început („mă cheamă X")
și verifică după compresie că mai știe.

### 2.5 Scalability & Extensibility (2p) — ~2h
- E despre arhitectură, nu funcționalități: tool-urile se adaugă doar cu un fișier
  nou în `tools/` + înregistrare; facts/procedures doar cu fișier + intrare în
  registry, fără să atingi codul. Deja stai bine — livrabilul e un README.

> 📍 **Unde în cod**
> - Fără funcții noi. `README.md` nou în `lab_5_skel/` cu secțiunile: „Cum adaugi un
>   tool" (fișier nou în `tools/` după șablonul `lucky_number_tool.py` + o linie în
>   `tools/tools.py`) și „Cum adaugi un document" (fișier .md + intrare în
>   `registry.json`, zero cod modificat).

### 2.6 Code Quality (2p) — ~2h (pass final)
- O singură instanță `EmbeddingsClient` creată în `Agent.__init__`, nu la fiecare mesaj
  (`agent.py:43` — se creează la FIECARE `process_message`).
- `utils.py` — `tiktoken.get_encoding(...)` la nivel de modul (acum se recreează la
  fiecare apel); docstring corectat („word tokens" nu mai e adevărat).
- `embeddings_client.py:103` — print-ul „Found X chunks" devine opțional/logging.
- Comentariile stale din `agent.py` (TODO 2.4 rezolvat) și `conversation_context.py`
  (hinturile lungi din compress_history pot fi comprimate într-un docstring).
- Verificare valori hardcodate; docstrings, type hints, nume clare.
- Fă asta ULTIMUL, ca un code review pe tine însuți.

**Timp total secțiunea 2 rămasă: ~4–6 ore**

---

## 3. Optional Enhancements — starea actuală + noua direcție

### 🎁 Aproape gratis — 2 din 4 FĂCUTE
| Enhancement | Puncte | Status |
|---|---|---|
| Dedicated Embedding + Chat Model | 2p | 🟨 **AI DEJA**: qwen3-embedding (Ollama, local) pentru embeddings + gpt-5-mini (Azure) pentru chat. Doar documentează în README |
| Embedding Cache | 2p | 🟨 FĂCUT (exists + mtime check) — repari bug-ul 5 (mtime pe subfoldere) și documentezi |
| Retrieval Thresholds & Tuning | 2p | ⬜ ai threshold + top-N; adaugă în README un mic experiment: scoruri relevant vs. irelevant |
| Chunk Overlap Strategy | 2p | ✅ FĂCUT — `CHUNK_OVERLAP = 20`, pas = `CHUNK_SIZE - CHUNK_OVERLAP`. Nu uita: după orice schimbare de chunking ștergi `embeddings.json` |

### 🖥️ Interfața — DECIZIA NOUĂ: OpenWebUI fără Docker + backend OpenAI-compatible

Calea B originală (UI custom în `static/index.html`) se înlocuiește cu ceva mai
valoros: **agentul devine un serviciu OpenAI-compatible**, iar interfața e
**OpenWebUI** — un chat UI matur, cu login per utilizator (ne dă multi-user aproape
gratis) și istoric de conversații.

**Punctele vizate**: HTTP Backend Service (3p) + REST API Endpoints (2p) +
Multi-user Support (3p) = **8p** de cod propriu. (Minimal Web UI 3p — de întrebat
profesorul dacă OpenWebUI se punctează; UI-ul nu e scris de tine, dar integrarea da.)

**Arhitectura**:
```
OpenWebUI (uv, Python 3.11, port 8080)
    │  POST /v1/chat/completions  (+ header X-OpenWebUI-User-Id)
    ▼
api.py — FastAPI, port 8000 (NOU, ~150 linii)
    │  un Agent + ConversationContext PER USER (dict {user_id: Agent})
    ▼
Agent → RAG (qwen3-embedding local) → gpt-5-mini (Azure) → tools
```

**De ce merge fără Docker**: OpenWebUI se instalează și cu pip — DAR cere Python
3.11 (3.14 al tău nu e suportat). Soluția: `uv`, care își descarcă singur un Python
3.11 izolat: `pip install uv`, apoi `uv tool install --python 3.11 open-webui`,
apoi `open-webui serve`. Zero Docker, zero atingere a mediului tău de proiect.

**Detalii cheie** (complet în `PLAN_IMPLEMENTARE_SONNET.md`):
- `api.py` expune `GET /v1/models` și `POST /v1/chat/completions` — inclusiv
  **streaming SSE** (OpenWebUI cere `stream: true` by default).
- OpenWebUI își trimite TOT istoricul lui la fiecare request; noi îl ignorăm și
  folosim doar ULTIMUL mesaj user — contextul (cu RAG, tools, compresie, tokeni)
  trăiește server-side, per user. Așa toate feature-urile de laborator rămân active.
- Multi-user: OpenWebUI trimite `X-OpenWebUI-User-Id` dacă pornești serverul cu
  `ENABLE_FORWARD_USER_INFO_HEADERS=True`.
- Capcană: OpenWebUI face request-uri EXTRA (generare titlu/tag-uri conversație) —
  se dezactivează din Admin Settings sau se detectează și se răspunde stateless.
- `main.py` rămâne neatins, ca CLI alternativ.

**Calea A (CLI cu rich)** — devine redundantă cu OpenWebUI ca interfață principală;
o sari, sau o faci doar dacă vrei +2–4p ușoare la final.

### 💾 Persistence & Sessions — se leagă natural de multi-user (~2–3h pentru 5p)
- Session Management (2p): `save_to_file`/`load_from_file` în `ConversationContext`.
- Multiple Conversations per User (2p): folder `sessions/` cu fișier per user
  (`sessions/<user_id>.json`) — multi-user din `api.py` îți dă asta aproape gratis;
  pentru CLI, listare/alegere la pornire.
- Export/Import (1p): aceleași două metode cu o cale aleasă de user.

> 📍 **Unde în cod (Sessions)**
> - Metode NOI în `conversation_context.py`: `save_to_file(path)` / `load_from_file(path)`
>   — `json.dump`/`json.load` pe `self.messages` (la load NU dublezi system prompt-ul:
>   încarci doar mesajele user/assistant peste cel proaspăt asamblat).
> - `api.py`: save după fiecare mesaj (sau la shutdown), load la primul request al userului.
> - `main.py`: save la `exit`, load la pornire.

### 🔧 AI Features
- Extra Tools (1p/tool, max 3p): ✅ **FĂCUT** — 7 tool-uri în `tools/`.

### 📊 Observability (dacă mai rămâne timp, ~2–3h pentru 4p)
- Structured Logging (2p) + Performance Metrics (2p) — neschimbate față de planul vechi.

### ❌ Ce NU recomand (efort mare / punctaj mic)
- Dynamic Tool Discovery (3p), Parallel Tool Execution (3p), Multi-step Tool
  Reasoning (4p), Automatic Model Selection (4p), Incremental Re-indexing (3p) —
  neschimbat față de planul vechi.

---

## 4. Buget de timp total (scenarii, actualizat)

| Scenariu | Conținut | Punctaj estimat | Timp rămas |
|---|---|---|---|
| **Minim solid** | Prețuri + bug-fix-uri + 2.3/2.5/2.6 | 10p + 12p = 22p | ~1 zi |
| **Recomandat (noul plan)** | + README-uri (tuning/dedicated: 4p) + overlap/cache deja făcute (4p) + `api.py` + OpenWebUI + multi-user (8p) + Sessions (5p) + tools (3p) | **~46p** | ~2–3 zile |
| **Maxim** | + Observability (4p) | ~50p | +3h |

## 5. Ordinea de lucru recomandată

1. ~~Securitate git~~ ✅
2. Prețuri 2.0/10.0 în config — 1 min
3. Bug-fix-urile 1–5 din „Bug-uri deschise" — 1–2h
4. 2.3 (TOP_N + doc) — 1h
5. Sessions (`save_to_file`/`load_from_file`) — pregătește terenul pentru api.py
6. `api.py` + OpenWebUI + multi-user — ~1 zi
7. README (2.5 + tuning + dedicated models + arhitectură)
8. Code Quality pass FINAL peste tot (2.6)
9. Observability dacă rămâne timp

*Regula de aur: commit după fiecare punct bifat, nu la final.*

**Execuția pașilor 2–8 e detaliată pentru Claude Sonnet în `PLAN_IMPLEMENTARE_SONNET.md`.**
