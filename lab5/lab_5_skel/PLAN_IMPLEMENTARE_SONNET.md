# Plan de implementare pentru Claude Sonnet — ce a mai rămas din proiect

> **Cine ești**: agentul care execută acest plan, pas cu pas, în folderul
> `lab5/lab_5_skel/`. Contextul complet al proiectului e în `PLAN_SESIUNEA6.md`.
>
> **Ce e proiectul**: chatbot educațional „Gem" (profesor de CS) — RAG peste
> `knowledge/`, tool calling, token/cost tracking, compresie de context.
> Chat model: `gpt-5-mini` pe Azure AI Foundry (cheie în env `CHATGPT_API_KEY`).
> Embeddings: `qwen3-embedding:latest` pe Ollama local (`http://localhost:11434`).
>
> **Reguli de lucru**:
> - NU rescrie ce funcționează deja; fă modificări minimale, în stilul codului existent.
> - Codul e scris de un student care învață — păstrează-l simplu și lizibil, fără
>   abstracțiuni fanteziste. Comentarii doar unde e nevoie.
> - Commit după fiecare etapă bifată (mesaje scurte, în engleză).
> - Rulează `python main.py` după fiecare etapă ca smoke test (necesită Ollama pornit
>   și `CHATGPT_API_KEY` setat; dacă lipsesc, verifică măcar că importurile merg:
>   `python -c "import agent, api"`).
> - Ordinea etapelor de mai jos NU e negociabilă — bug-fix-urile vin primele.

---

## Etapa 1 — Fix obligatoriu: prețurile (1 minut)

`config.py:34-35` — cerința din PPT (Ex. 3) cere exact:

```python
INPUT_TOKEN_PRICE_PER_MILLION = 2.0
OUTPUT_TOKEN_PRICE_PER_MILLION = 10.0
```

Acum sunt 30/70. Schimbă doar valorile.

---

## Etapa 2 — Bug-fix-uri în `compress_history` (`conversation_context.py`)

### 2a. Pasul 4 — textul pentru rezumat e stricat (CRITIC)

Liniile 156–162: `"\n".join(...)` primește un f-string (deci intercalează `\n` între
caractere) și atribuirea suprascrie la fiecare iterație. Înlocuiește cu:

```python
lines = []
for m in old:
    lines.append(f"{m.get('role')}: {str(m.get('content') or '')}")
conversation_text = "\n".join(lines)
```

(Repară implicit și bug-ul `or None` → `"None"`.)

### 2b. Pasul 3 — `if` → `while` la mesajele tool

Linia 143: pot exista MAI MULTE mesaje `tool` consecutive la începutul lui `recent`
(tool call multiplu). Schimbă `if` în `while` (și păstrează guard pe listă nevidă):

```python
while recent and recent[0].get("role") == "tool":
    old.append(recent.pop(0))
```

Notă: mută și verificarea `len(messages) <= 1 + config.KEEP_RECENT_MESSAGES: return`
ÎNAINTE de slicing (acum e după — merge, dar e derutant).

### 2c. Pasul 5 — rezumatul poate fi un mesaj de eroare

După 2.2, `generate_response` NU aruncă excepții — la eșec întoarce textul erorii
drept `content`. Verificarea actuală prinde doar string gol. Adaugă o detecție simplă:
mesajele de eroare din `llm_client.py` încep toate cu fraze cunoscute („The model",
„Could not reach", „Too many requests"). Cea mai curată soluție minimală: în
`llm_client.py`, la fiecare return de eroare adaugă un flag în dict:

```python
return {"message": {"content": error_message}, "error": True}
```

(la fel pentru cazul „unreadable response"), iar în `compress_history`:

```python
if response.get("error"):
    summary = None
```

Verifică că `agent.py` nu se strică — el citește doar `response["message"]`, deci
flag-ul în plus e inofensiv. Bonus: în `agent.py::process_message`, dacă primul
răspuns are `error: True`, nu mai are sens al doilea request — dar NU schimba fluxul
dacă nu e trivial; e opțional.

### 2d. Curățenie comentarii

- Șterge comentariul stale din `agent.py:38-40` („Decomentează linia de mai jos" —
  apelul e deja decomentat).
- În `compress_history`, comprimă blocurile lungi de HINT/TODO (își făcuseră treaba
  pedagogică) într-un docstring scurt care descrie strategia. Păstrează docstring-ul
  existent al metodei.

### Test etapa 2

Setează temporar `MAX_CONTEXT_TOKENS = 2000` în config, rulează `main.py`, poartă
4–5 schimburi (primul: „Numele meu este Cristian"), apoi întreabă „cum mă cheamă?".
Trebuie: (a) fără crash, (b) răspunsul corect din rezumat, (c) `print` temporar pe
`len(self.messages)` să arate că istoricul chiar s-a comprimat. Revino la 4096.

---

## Etapa 3 — Bug-fix embedding cache (`embedding_generator.py`)

`os.path.getmtime("knowledge")` nu se schimbă când editezi fișiere din SUBFOLDERE
(`knowledge/facts/*.md` etc.) → cache-ul nu se invalidează. Înlocuiește cu mtime-ul
maxim peste toate fișierele:

```python
def _knowledge_mtime():
    latest = 0.0
    for root, _dirs, files in os.walk("knowledge"):
        for name in files:
            latest = max(latest, os.path.getmtime(os.path.join(root, name)))
    return latest
```

și folosește `_knowledge_mtime() < os.path.getmtime(EMBEDDINGS_FILE)` în check.

**Test**: `touch` (sau re-salvează) un fișier din `knowledge/facts/`, rulează
`main.py` → trebuie să regenereze; rulează iar fără modificări → „Skipping generation".

---

## Etapa 4 — 2.3 Cost Optimization

- `config.py:26`: `TOP_N = 20` → `TOP_N = 4`.
- Șterge `embeddings.json` NU e necesar aici (top_n e la query, nu la indexare).
- Documentarea strategiei intră în README (Etapa 7) — nu scrie README acum.

---

## Etapa 5 — Sessions (`conversation_context.py` + `main.py`)

### 5a. Metode noi pe `ConversationContext`

```python
def save_to_file(self, path):
    # json.dump pe self.messages (fără system prompt? NU — salvează tot,
    # dar la load îl arunci) + input_tokens/output_tokens
def load_from_file(self, path):
    # încarcă mesajele SĂRIND peste orice mesaj cu role == "system" de la
    # început (system promptul se reasamblează proaspăt în __init__);
    # restaurează contoarele de tokeni; FileNotFoundError/JSONDecodeError
    # → warning + pornește gol (stilul de error handling existent)
```

Format fișier sugerat: `{"messages": [...], "input_tokens": N, "output_tokens": N}`.
Atenție la subtilitate: mesajele `system` injectate MID-conversație („Relevant
knowledge...", „Summary of the earlier conversation...") pot fi păstrate — sari doar
peste PRIMUL mesaj dacă e system (system promptul mare). Cel mai simplu: la save,
scrie `self.messages[1:]`; la load, `self.messages = [self.messages[0]] + cele încărcate`.

- Folder nou `sessions/` (creat cu `os.makedirs(exist_ok=True)`); adaugă `sessions/`
  în `.gitignore`.
- Constantă `SESSIONS_DIR = "sessions"` în `config.py`.

### 5b. CLI (`main.py`)

- La pornire: dacă există `sessions/cli_default.json`, întreabă
  `Continui conversația anterioară? [y/n]` → load.
- La `exit`: save în același fișier.
- Export/Import (1p): două comenzi în bucla de chat — `save <nume>` și `load <nume>`
  → `sessions/<nume>.json` prin aceleași două metode. Nu complica.

**Test**: conversație scurtă → `exit` → repornește → `y` → întreabă ceva ce i-ai
spus înainte; verifică și că `input_tokens` continuă acumularea, nu pornește de la 0.

---

## Etapa 6 — `api.py`: backend OpenAI-compatible + multi-user (MIEZUL)

Fișier NOU `api.py` în `lab_5_skel/`. Adaugă `fastapi` și `uvicorn` în
`requirements.txt` și instalează-le.

### 6a. Schelet și stare per user

```python
import json
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

import config
from agent import Agent
from conversation_context import ConversationContext
from embedding_generator import embedding_generator
from llm_client import LLMClient
from tools.tools import tools

app = FastAPI()
llm_client = LLMClient()
agents = {}  # user_id -> Agent (fiecare cu ConversationContext propriu)

@app.on_event("startup")
def startup():
    embedding_generator()

def get_agent(user_id):
    if user_id not in agents:
        context = ConversationContext()
        context.load_from_file(session_path(user_id))   # istoric persistent per user
        agents[user_id] = Agent(llm_client, context, tools=tools)
    return agents[user_id]
```

`session_path(user_id)` → `os.path.join(config.SESSIONS_DIR, f"{user_id}.json")` —
sanitizează user_id (doar alfanumerice/`-`/`_`) ca să nu iasă path traversal.

### 6b. `GET /v1/models`

OpenWebUI îl apelează ca să populeze lista de modele:

```python
@app.get("/v1/models")
def models():
    return {"object": "list",
            "data": [{"id": "gem-agent", "object": "model", "owned_by": "lab5"}]}
```

### 6c. `POST /v1/chat/completions`

Comportament:
1. Citește body-ul JSON. Extrage `user_id` din header `x-openwebui-user-id`
   (fallback: `"default"`).
2. **Ignoră istoricul trimis de OpenWebUI** — ia doar ULTIMUL mesaj cu
   `role == "user"` din `body["messages"]`. Contextul real (RAG, tools, compresie,
   token tracking) trăiește server-side în `ConversationContext`-ul userului.
3. `answer = get_agent(user_id).process_message(user_text)` — apoi
   `context.save_to_file(session_path(user_id))`.
4. Răspunde în formatul OpenAI. **Trebuie suportat și `stream: true`** (OpenWebUI îl
   trimite by default):

Non-streaming (`stream` absent sau false):

```python
{
  "id": f"chatcmpl-{uuid.uuid4().hex}",
  "object": "chat.completion",
  "created": int(time.time()),
  "model": "gem-agent",
  "choices": [{"index": 0,
               "message": {"role": "assistant", "content": answer},
               "finish_reason": "stop"}],
  "usage": {"prompt_tokens": ctx.input_tokens,
            "completion_tokens": ctx.output_tokens,
            "total_tokens": ctx.input_tokens + ctx.output_tokens},
}
```

Streaming (`stream: true`) — SSE cu `StreamingResponse(media_type="text/event-stream")`.
Agentul nu produce streaming real, deci trimite răspunsul complet într-un singur chunk
(pattern standard de „fake streaming"), apoi chunk-ul de final și `[DONE]`:

```python
def sse():
    chunk = {"id": rid, "object": "chat.completion.chunk", "created": created,
             "model": "gem-agent",
             "choices": [{"index": 0, "delta": {"role": "assistant",
                                                "content": answer},
                          "finish_reason": None}]}
    yield f"data: {json.dumps(chunk)}\n\n"
    done = {"id": rid, "object": "chat.completion.chunk", "created": created,
            "model": "gem-agent",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    yield f"data: {json.dumps(done)}\n\n"
    yield "data: [DONE]\n\n"
```

Opțional (nice-to-have): sparge `answer` pe cuvinte și yield-uie mai multe chunk-uri
ca să se vadă efectul de typing în UI.

### 6d. Capcana request-urilor de „task" (titlu/tag-uri)

OpenWebUI trimite request-uri EXTRA către același model pentru generarea titlului și
tag-urilor conversației. Dacă trec prin `process_message`, poluează contextul userului
(RAG + tool-uri + tracking pe un prompt intern al UI-ului).

Apărare în două straturi:
1. În `api.py`: detectează-le — prompturile de task OpenWebUI conțin marcajul
   `### Task:`. Dacă ultimul mesaj user conține `### Task:`, NU trece prin agent:
   apelează direct `llm_client.generate_response([...])` stateless cu mesajele primite
   și întoarce răspunsul (același format ca la 6c).
2. În documentația de setup (Etapa 8): recomandă oricum dezactivarea generării de
   titlu/tag-uri din Admin Settings → Interface.

### 6e. Multi-user

Nimic în plus de codat — vine din `agents = {user_id: Agent}` + header. De verificat
doar că `ConversationContext.__init__` NU are stare partajată între instanțe.
ATENȚIE cunoscută: tool-urile scriu în `student_records.json` COMUN — e OK pentru lab
(profesorul are un singur catalog), doar menționează în README.

### Rulare

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

### Test etapa 6 (fără OpenWebUI, cu curl/PowerShell)

```powershell
curl http://127.0.0.1:8000/v1/models
curl -X POST http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -H "x-openwebui-user-id: alice" -d '{"model":"gem-agent","messages":[{"role":"user","content":"Salut! Ma numesc Alice."}]}'
curl -X POST ... -H "x-openwebui-user-id: bob" -d '... "Cum ma cheama?" ...'
```

Bob NU trebuie să știe numele lui Alice; un al doilea request ca `alice` cu
„cum mă cheamă?" trebuie să răspundă „Alice". Testează și cu `"stream": true`
(verifici că iese `data: ...` + `data: [DONE]`).

---

## Etapa 7 — README.md (acoperă 2.5 + documentările de 2p)

Fișier NOU `README.md` în `lab_5_skel/`, în engleză, cu secțiunile:

1. **Overview & Architecture** — diagrama User → (CLI `main.py` | OpenWebUI → `api.py`)
   → Agent → ConversationContext → RAG (qwen3-embedding, Ollama) → gpt-5-mini (Azure)
   → tools. Cum se rulează (env vars, Ollama, `python main.py`, `uvicorn api:app`).
2. **Scalability & Extensibility (2.5)** — „How to add a tool" (fișier nou în `tools/`
   după șablonul `lucky_number_tool.py` + o linie în `tools/tools.py`) și „How to add
   a knowledge document" (fișier `.md` + intrare în `registry.json`, zero cod).
3. **Cost Optimization (2.3)** — strategia: always_load doar pentru esențial, retrieval
   cu `TOP_N=4` + `SIMILARITY_THRESHOLD=0.5`, compresie de context la
   `MAX_CONTEXT_TOKENS`, token/cost tracking. Include un mini-raport măsurat: rulează
   o întrebare și raportează tokenii promptului final vs. dimensiunea totală a KB
   (numără cu `count_tokens` pe toate documentele).
4. **Retrieval Thresholds & Tuning (2p)** — mic experiment REAL: 3 întrebări relevante
   + 3 irelevante, tabel cu scorurile de similaritate observate (istoric: relevantele
   ieșeau 0.51–0.66), concluzia pentru threshold=0.5 și top_n=4. Rulează experimentul,
   nu inventa numerele.
5. **Dedicated Embedding + Chat Model (2p)** — de ce embeddings local (gratuit, datele
   nu pleacă, latență mică) + chat pe Azure (calitate), și că schimbarea oricăruia e
   o linie în `config.py`.
6. **Error Handling & Fallbacks (2.1/2.2)** — pe scurt, comportamentul la: Ollama oprit,
   endpoint indisponibil, cheie greșită, fișiere lipsă/corupte, retrieval gol.
7. **Multi-user & Sessions** — cum funcționează `api.py` + `sessions/`, limitarea cu
   `student_records.json` comun.
8. **OpenWebUI setup fără Docker** — conținutul din Etapa 8.

---

## Etapa 8 — OpenWebUI fără Docker (setup + documentare)

**Constrângere hard**: mediul proiectului e Python 3.14 — `pip install open-webui`
NU merge (suportă 3.11–3.12). Fără Docker. Soluția: `uv`, care își aduce propriul
Python 3.11 izolat, fără să atingă mediul proiectului:

```powershell
pip install uv
uv tool install --python 3.11 open-webui
# pornire (prima oară durează câteva minute):
$env:ENABLE_FORWARD_USER_INFO_HEADERS = "True"   # trimite X-OpenWebUI-User-Id spre api.py
open-webui serve --port 8080
```

Configurare în browser la `http://localhost:8080`:
1. Primul cont creat devine ADMIN. Creează apoi un al doilea cont (alt browser /
   incognito) ca să demonstrezi multi-user.
2. Admin Panel → Settings → **Connections** → OpenAI API: URL `http://127.0.0.1:8000/v1`,
   API key: orice string (ex. `dummy`). Dezactivează conexiunea Ollama directă dacă
   apare (altfel vede modelele Ollama pe lângă `gem-agent`).
3. Admin Panel → Settings → **Interface** → dezactivează Title Auto-Generation și
   Tags Generation (plasă de siguranță pe lângă detecția `### Task:` din api.py).
4. Selectează modelul `gem-agent` și conversează.

**Test end-to-end (demo-ul final)**:
- User A (admin): „Mă numesc Ana, evaluează acest cod: ..." → agentul folosește
  tool-urile, răspunde în persona Gem.
- User B (al doilea cont): „Cum mă cheamă?" → NU știe de Ana.
- Repornește `api.py` → contextele se reîncarcă din `sessions/` (persistență).
- `python main.py` merge în paralel, neatins.

Dacă `uv tool install` eșuează pe rețeaua locală, fallback: instalează Python 3.11
de pe python.org alături de 3.14, `py -3.11 -m venv webui_env`, activezi și
`pip install open-webui`. Documentează varianta care a mers.

---

## Etapa 9 — 2.6 Code Quality (pass FINAL, după ce totul merge)

- `agent.py::__init__`: `self.embeddings_client = EmbeddingsClient()` o singură dată;
  `process_message` folosește instanța (acum creează una la FIECARE mesaj —
  `agent.py:43`).
- `utils.py`: mută `encoding = tiktoken.get_encoding("cl100k_base")` la nivel de modul
  (acum se recreează la fiecare apel); corectează docstring-ul („word tokens" e fals).
- `embeddings_client.py:103`: print-ul „Found X chunks" — pune-l sub un flag
  `config.DEBUG = False` sau șterge-l.
- `conversation_context.py`: `import utils as uti` → `from utils import count_tokens`
  (consistent cu restul); scoate importul duplicat al `SYSTEM_PROMPT` (e importat și
  prin `config`).
- Caută hardcodări rămase: `grep -n "embeddings.json\|localhost\|11434" *.py` — tot
  ce nu vine din `config.py` se mută acolo.
- Docstrings scurte pe metodele noi (`save_to_file`, `load_from_file`, endpoints).
- La FINAL rulează tot smoke-test-ul: CLI + curl pe api + OpenWebUI.

---

## Checklist de predare

- [ ] `config.py`: prețuri 2.0/10.0, `TOP_N=4`
- [ ] `compress_history`: cele 3 bug-uri reparate + test de memorie trecut
- [ ] cache embeddings: invalidare corectă pe subfoldere
- [ ] `sessions/`: save/load în CLI și per-user în API; `sessions/` în `.gitignore`
- [ ] `api.py`: `/v1/models` + `/v1/chat/completions` (stream + non-stream) + multi-user + filtru `### Task:`
- [ ] OpenWebUI instalat prin uv (fără Docker), conectat, 2 useri demonstrați
- [ ] `README.md` complet (arhitectură, extensibilitate, cost, tuning cu numere reale, setup)
- [ ] code quality pass + comentarii stale șterse
- [ ] `requirements.txt` actualizat (fastapi, uvicorn)
- [ ] commit per etapă, fără chei API în cod
