# Plan proiect final — Sesiunea 6 (Orchestrare și Automatizare)

Estimările presupun ritmul tău actual (student + Copilot ca autocomplete). Punctajele sunt din PPT.

> **Schimbare majoră față de versiunea anterioară a planului**: proiectul a migrat de pe
> Gemini pe **Azure AI Foundry / Azure OpenAI** (`gpt-5-mini`, cheie în env var
> `CHATGPT_API_KEY`), iar embeddings-urile pe **qwen3-embedding** (Ollama, local).
> Orice mențiune veche de „Gemini" / „bge-m3" din notițe se citește acum așa.
>
> **Ce mai e de implementat** e detaliat pas cu pas în `PLAN_IMPLEMENTARE_SONNET.md`
> — planul de execuție pentru Claude Sonnet.
>
> **UPDATE 17 iulie**: Sonnet a executat toate cele 9 etape din
> `PLAN_IMPLEMENTARE_SONNET.md` — prețuri, cele 4 bug-uri din `compress_history` +
> cache-ul de embeddings, `TOP_N`, Sessions, `api.py` (backend OpenAI-compatible +
> multi-user, testat end-to-end), `README.md` complet cu experimentul de retrieval
> rulat cu numere reale, și pass-ul de code quality.
>
> **UPDATE 17 iulie (2) — decizia de interfață REVENITĂ**: OpenWebUI a fost
> încercat, instalat și configurat, dar s-a dovedit mai multă frecare decât
> valoare — auto-detectează Ollama local și amestecă modelele lui de embeddings
> (`qwen3-embedding`, `bge-m3` etc.) în ACELAȘI selector cu `gem-agent`, ceea ce
> a dus la alegerea modelului greșit de două ori la rând în timpul testării. Plus
> instalarea unui runtime Python 3.11 separat + 258 de pachete (~500MB) doar ca
> să pornească o fereastră de chat, pentru o cerință („Minimal Web UI”, 3p) care
> oricum trebuie să fie codul TĂU, nu o integrare. Decizie: **OpenWebUI complet
> dezinstalat** (`uv tool uninstall open-webui`), înlocuit cu o **interfață web
> proprie, statică** (`static/index.html` + `style.css` + `app.js`, vanilla JS,
> fără framework, fără build), servită direct de `api.py` — un singur proces, un
> singur port. Multi-user prin prompt simplu de nume la intrare (`localStorage`
> în browser), nu login OpenWebUI. Detalii complete în README.md §7-8 și jurnal.

---

## 🗺️ Harta rapidă — ce task, ce fișier, ce funcție

| Task | Fișier principal | Ce faci acolo | Status |
|---|---|---|---|
| count_tokens cu tiktoken (oblig., Ex.1) | `utils.py` | ✅ `tiktoken.get_encoding("cl100k_base")` | ✅ |
| Token tracking (oblig., Ex.2) | `conversation_context.py` + `agent.py` + `main.py` | ✅ atribute + metode (tu) + poziția apelurilor în agent reparată (Claude); main.py curățat (tu) | ✅ |
| Constante preț (oblig., Ex.3) | `config.py` | ✅ 2.0 / 10.0 (Sonnet) | ✅ |
| Titluri secțiuni (oblig.) | `conversation_context.py` | ✅ heading din `name` (tu) + spațiul lipsă `## ` (Claude) | ✅ |
| Migrare Azure OpenAI | `config.py` + `llm_client.py` + `embeddings_client.py` | ✅ endpoint Azure + `_headers()` (api-key vs Bearer), model `gpt-5-mini`, embeddings `qwen3-embedding` | ✅ |
| 2.1 Fallback | `llm_client.py` + `agent.py` | ✅ retry (tu) + mesaje pe tip de eroare (Claude) + ramura `else:` la search (tu) | ✅ |
| 2.2 Error handling | `llm_client.py`, `embeddings_client.py`, `embedding_generator.py`, `document_chunker.py`, `conversation_context.py` | ✅ implementat + testat (fișiere lipsă/corupte, Ollama oprit, cheie invalidă, timeout) | ✅ |
| 2.3 Cost optimization | `config.py` + README | ✅ `TOP_N=4`, strategie documentată în README §3 (Sonnet) | ✅ |
| 2.4 Context recycling | `conversation_context.py` + `agent.py` | ✅ TODO-uri + cele 4 bug-uri reparate și testate (Sonnet: pasul 4 mutila textul, pasul 5 putea băga erori în istoric, `if`→`while` la mesaje tool, `or None`→`or ""`) | ✅ |
| 2.5 Scalability | `README.md` | ✅ secțiunea „How to add a tool" / „How to add a knowledge document" (Sonnet) | ✅ |
| 2.6 Code quality | `agent.py`, `utils.py`, `embeddings_client.py`, `conversation_context.py` | ✅ o singură `EmbeddingsClient` per Agent, encoding tiktoken la nivel de modul, print de debug sub `config.DEBUG`, import curățat (Sonnet) | ✅ |
| Chunk overlap (2p) | `document_chunker.py` + `config.py` | ✅ `CHUNK_OVERLAP = 20`, pasul buclei e `CHUNK_SIZE - CHUNK_OVERLAP` | ✅ |
| Embedding cache (2p) | `embedding_generator.py` | ✅ exists-check + `_knowledge_mtime()` cu `os.walk` (Sonnet — fix pe subfoldere) | ✅ |
| Retrieval tuning (2p) | `config.py` + README | ✅ experiment REAL rulat (3 relevante/3 irelevante), scoruri 0.67–0.81 vs. 0 pentru irelevante, în README §4 (Sonnet) | ✅ |
| Dedicated models (2p) | README | ✅ documentat în README §5 (Sonnet) | ✅ |
| Sessions (2p+2p+1p) | `conversation_context.py` + `main.py` | ✅ `save_to_file`/`load_from_file` + comenzi `save`/`load <name>` în CLI, `sessions/` (Sonnet) | ✅ |
| **Backend OpenAI-compatible (3p+2p)** | `api.py` (nou) | ✅ `GET /v1/models` + `POST /v1/chat/completions` cu streaming SSE, testat cu FastAPI TestClient (Sonnet) | ✅ |
| **Multi-user Support (3p)** | `api.py` | ✅ dict `{user_id: Agent}` pe header `X-User-Id`, izolare verificată prin test (alice ≠ bob) (Sonnet) | ✅ |
| **Interfață Web custom (Minimal Web UI, 3p)** | `static/` (nou) + `api.py` | ✅ `index.html`/`style.css`/`app.js` proprii, servite de `api.py`, cu typing effect real (SSE server-side) și username prin `localStorage` (Sonnet) — cod 100% al studentului, fără dependență externă | ✅ |
| Extra tools (3p) | `tools/` | ✅ 7 tool-uri implementate și înregistrate în `tools/tools.py` | ✅ |
| Knowledge nou | `knowledge/` | ✅ 3 facts + 4 procedures pe persona profesor, registries actualizate | ✅ |
| Identity extins | `knowledge/prompts/identity.md` | ✅ regulile 9–12 + secțiunea Persona/Gender | ✅ |
| API key în env var | `config.py` | ✅ `os.environ.get("CHATGPT_API_KEY", "")` | ✅ |

Detaliile fiecărui rând sunt mai jos, în secțiunea lui, în blocurile „📍 Unde în cod".

---

## ✅ Bug-uri reparate (găsite la review-ul din 17 iulie, reparate de Sonnet aceeași zi)

Toate cele 7 bug-uri de mai jos au fost reparate și verificate cu teste izolate
(fake `llm_client`, `FastAPI TestClient`) — vezi jurnalul mai jos pentru detalii de
testare:

1. ~~**`compress_history` Pasul 4**~~ — FIXAT: textul pentru rezumat se construiește
   acum ca listă de linii `"{rol}: {content}"`, apoi un singur `"\n".join()` după
   buclă. Verificat cu test: toate mesajele vechi ajung intacte în textul trimis la
   LLM (înainte, doar ultimul mesaj ajungea, mutilat literă cu literă).
2. ~~**`compress_history` Pasul 5`**~~ — FIXAT: `llm_client.py` întoarce acum
   `{"error": True}` la orice eșec; `compress_history` verifică acest flag înainte de
   a folosi `content`-ul ca rezumat. Verificat cu test: un LLM care „pică" nu mai
   lasă text de eroare în istoric, cade pe sliding window.
3. ~~**`compress_history` Pasul 3`**~~ — FIXAT: `if` → `while` la mutarea mesajelor
   `tool` din capul lui `recent` în `old`.
4. ~~**`compress_history` Pasul 4` (`or None`)~~ — FIXAT: `str(m.get("content") or "")`.
5. ~~**Embedding cache**~~ — FIXAT: `_knowledge_mtime()` în `embedding_generator.py`
   folosește `os.walk` peste tot folderul `knowledge/`, nu doar mtime-ul folderului
   de top-level.
6. ~~**Prețuri**~~ — FIXAT: `config.py` are acum `2.0` / `10.0`.
7. ~~Cosmetic~~ — comentariul stale din `agent.py` șters; docstring-ul din
   `utils.py::count_tokens` corectat.

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

**Făcute de SONNET pe 17 iulie (executarea PLAN_IMPLEMENTARE_SONNET.md):**
- `config.py` — prețuri 2.0/10.0; `TOP_N` 20→4; `DEBUG=False`; `SESSIONS_DIR="sessions"`
- `conversation_context.py::compress_history` — cele 4 bug-uri reparate (vezi secțiunea
  de mai sus); import `uti` alias înlocuit cu `from utils import count_tokens`
- `conversation_context.py` — metode noi `save_to_file`/`load_from_file` (Sessions)
- `llm_client.py` — răspunsurile de eroare întorc acum și `"error": True`
- `embedding_generator.py` — `_knowledge_mtime()` cu `os.walk` (fix cache)
- `agent.py` — o singură `EmbeddingsClient` per `Agent` (creată în `__init__`,
  refolosită în `process_message`); comentariu stale șters
- `utils.py` — `_encoding` la nivel de modul; docstring corectat
- `embeddings_client.py` — print „Found X chunks" mutat sub `config.DEBUG`
- `main.py` — integrare sessions (load la pornire cu confirmare, save la exit,
  comenzi `save <nume>` / `load <nume>`); import nefolosit `count_tokens` scos
- **`api.py` (fișier nou)** — backend FastAPI OpenAI-compatible: `GET /v1/models`,
  `POST /v1/chat/completions` (streaming SSE + non-streaming), multi-user pe
  `X-OpenWebUI-User-Id` cu un `Agent`/`ConversationContext` per user, persistență
  automată în `sessions/`, filtru pentru request-urile interne `### Task:` ale
  OpenWebUI (răspuns stateless, nu ating contextul niciunui user)
- **`README.md` (fișier nou)** — arhitectură, cost optimization cu numere măsurate
  (4360 tokeni KB completă vs. 265 always-load), experiment de retrieval tuning RULAT
  efectiv pe embeddings reale (scoruri 0.669/0.708/0.813 pentru întrebări relevante,
  0 chunk-uri pentru cele irelevante)
- `requirements.txt` — adăugat `fastapi`, `uvicorn`
- `.gitignore` — adăugat `lab5/lab_5_skel/sessions/`
- **Testare**: toate modulele importă curat; `compress_history` testat izolat (fallback
  sliding window, rezumare cu conversation_text corect, fallback la eroare de LLM);
  `api.py` testat end-to-end cu `FastAPI TestClient` — izolare multi-user confirmată
  (bob nu vede numele lui alice), filtrul `### Task:` confirmat, streaming SSE
  confirmat, persistență pe disc în `sessions/` confirmată (fișiere de test șterse
  după verificare)

**Făcute de SONNET pe 17 iulie (2) — reversarea OpenWebUI → interfață web proprie:**
- Instalat, testat și apoi **complet dezinstalat** OpenWebUI (`uv tool uninstall
  open-webui`), din cauza confuziei de model-picker (Ollama auto-detectat amestecă
  `qwen3-embedding`/`bge-m3` cu `gem-agent` în aceeași listă) și a greutății
  instalării (258 pachete, ~500MB) pentru o cerință care trebuie să fie codul
  studentului. Șters `.webui_secret_key` din rădăcina repo-ului.
- **`api.py`** — `USER_ID_HEADER` redenumit din `x-openwebui-user-id` în `x-user-id`;
  eliminat complet filtrul `### Task:` (`TASK_MARKER`) — era doar pentru
  request-urile interne ale OpenWebUI, acum mort; adăugat
  `app.mount("/", StaticFiles(directory="static", html=True))` la finalul
  fișierului (după rutele `/v1/...`, ca să nu le umbrească); `_stream_chunks`
  rescris ca generator async — sparge răspunsul pe cuvinte și trimite câte un
  chunk SSE per cuvânt cu `await asyncio.sleep(STREAM_CHUNK_DELAY_SECONDS)`
  (0.03s) între ele, ca frontend-ul să aibă un efect de typing REAL, nu doar unul
  simulat în JS.
- **`static/` (nou)** — `index.html` + `style.css` + `app.js`, vanilla JS fără
  framework/build: prompt de username la prima încărcare (`localStorage`), trimis
  ca header `X-User-Id` pe fiecare request; citește streaming-ul SSE cu
  `response.body.getReader()` și adaugă fiecare `delta.content` în bula
  asistentului pe măsură ce sosește; buton „Schimbă userul”.
- **Testare**: `TestClient` — static files (200/404 corecte, content-types corecte),
  `/v1/models` NEUMBRIT de mount (confirmă ordinea rutelor), izolare multi-user cu
  header-ul nou (alice/bob), streaming word-by-word (5 cuvinte → 5 chunk-uri SSE).
  Testat și pe server `uvicorn` REAL (nu doar `TestClient`): timing măsurat între
  chunk-uri ≈ 30-40ms, confirmă `asyncio.sleep` chiar funcționează pe evenimentul
  de bază, nu doar sincron în test.
- `README.md` §1/7/8 și `GHID_RULARE_TESTARE.md` §2/3 rescrise pentru noua interfață.

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

### 🖥️ Interfața — DECIZIA FINALĂ: interfață web proprie, servită de `api.py`

**Istoric scurt**: prima variantă era Calea B cu UI custom; apoi s-a încercat
OpenWebUI (instalat efectiv, configurat, testat) ca soluție „gratuită" pentru
Minimal Web UI + Multi-user; s-a dovedit mai multă frecare decât valoare —
Ollama local e auto-detectat de OpenWebUI și modelele lui de embeddings
(`qwen3-embedding`, `bge-m3`) apar în ACELAȘI selector cu `gem-agent`, ceea ce a
dus la alegerea modelului greșit de două ori în timpul testării, plus 258 de
pachete (~500MB, runtime Python 3.11 separat) doar ca să pornească o fereastră
de chat. **Decizie finală: OpenWebUI dezinstalat complet, înlocuit cu o
interfață web scrisă de la zero** — `static/index.html` + `style.css` +
`app.js` (vanilla JS, fără framework, fără build), servită direct de `api.py`.

**Punctele vizate**: HTTP Backend Service (3p) + REST API Endpoints (2p) +
Multi-user Support (3p) + **Minimal Web UI (3p, acum fără ambiguitate — e cod
100% al tău)** = **11p**.

**Arhitectura**:
```
Browser (static/index.html + app.js)
    │  POST /v1/chat/completions  (+ header X-User-Id, din localStorage)
    ▼
api.py — FastAPI, port 8000 (servește ȘI API-ul, ȘI fișierele statice)
    │  un Agent + ConversationContext PER USER (dict {user_id: Agent})
    ▼
Agent → RAG (qwen3-embedding local) → gpt-5-mini (Azure) → tools
```

**Detalii cheie**:
- `api.py` expune `GET /v1/models` și `POST /v1/chat/completions` — cu
  **streaming SSE real**: `_stream_chunks` sparge răspunsul complet al agentului
  (care nu e el însuși streaming) pe cuvinte și le trimite cu o mică pauză
  (`asyncio.sleep(0.03)`) între ele — efect de typing autentic, nu simulat în JS.
- Fișierele statice sunt montate cu `StaticFiles(directory="static", html=True)`
  la finalul fișierului, DUPĂ rutele `/v1/...` — altfel le-ar umbri (Starlette
  potrivește rutele în ordinea înregistrării).
- Multi-user: `app.js` cere un nume la prima încărcare, îl ține în
  `localStorage`, îl trimite ca header `X-User-Id` — fără login real, dar
  suficient să demonstreze izolarea per-user cerută de curs.
- `main.py` rămâne neatins, ca CLI alternativ.

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
| **Recomandat (noul plan)** | + README-uri (tuning/dedicated: 4p) + overlap/cache deja făcute (4p) + `api.py` + interfață web proprie + multi-user (11p) + Sessions (5p) + tools (3p) | **~49p** | ~2–3 zile |
| **Maxim** | + Observability (4p) | ~53p | +3h |

## 5. Ordinea de lucru recomandată

1. ~~Securitate git~~ ✅
2. Prețuri 2.0/10.0 în config — 1 min
3. Bug-fix-urile 1–5 din „Bug-uri deschise" — 1–2h
4. 2.3 (TOP_N + doc) — 1h
5. Sessions (`save_to_file`/`load_from_file`) — pregătește terenul pentru api.py
6. `api.py` + interfață web proprie (`static/`) + multi-user — ~1 zi
7. README (2.5 + tuning + dedicated models + arhitectură)
8. Code Quality pass FINAL peste tot (2.6)
9. Observability dacă rămâne timp

*Regula de aur: commit după fiecare punct bifat, nu la final.*

**Execuția pașilor 2–8 e detaliată pentru Claude Sonnet în `PLAN_IMPLEMENTARE_SONNET.md`.**
