# Ghid de rulare și testare

Document practic, pas cu pas, pentru tine — cum pornești proiectul și cum verifici
că fiecare bucată chiar funcționează. Pentru arhitectură/design vezi `README.md`;
pentru ce s-a schimbat și de ce, `PLAN_SESIUNEA6.md`.

---

## 0. Pregătire (o singură dată)

### 0.1 Activează mediul virtual

```powershell
cd c:\Users\preda.cristian\Desktop\work
my_env\Scripts\Activate.ps1
```

Prompt-ul PowerShell trebuie să înceapă cu `(my_env)`. Dependențele
(`fastapi`, `uvicorn`, `requests`, `tiktoken`, `ddgs`, `beautifulsoup4`) sunt deja
instalate acolo — dacă vreodată lipsește ceva:

```powershell
cd lab5\lab_5_skel
pip install -r requirements.txt
```

### 0.2 Cheia Azure

```powershell
$env:CHATGPT_API_KEY = "cheia-ta-azure"
```

Fără ea, orice request către `gpt-5-mini` întoarce mesajul de eroare „rejected the
API key" — codul nu crapă, dar nici nu răspunde util. Setează-o în fiecare sesiune
nouă de PowerShell (sau permanent din System Properties → Environment Variables).

### 0.3 Ollama pornit, cu modelul de embeddings

```powershell
ollama list
```

Trebuie să apară `qwen3-embedding:latest`. Dacă Ollama nu rulează deloc, pornește-l
(aplicația Ollama sau `ollama serve`). Fără el, chat-ul merge, dar FĂRĂ RAG
(„Semantic search skipped: ...").

### 0.4 Mergi în folderul proiectului

Toate comenzile de mai jos presupun că ești în:

```powershell
cd c:\Users\preda.cristian\Desktop\work\lab5\lab_5_skel
```

---

## 1. Testarea CLI-ului (`main.py`)

```powershell
python main.py
```

La prima pornire generează `embeddings.json` (poate dura — 29 de chunk-uri trimise
la Ollama). La pornirile ulterioare, dacă nu ai modificat nimic în `knowledge/`,
vezi „Knowledge base has not changed... Skipping generation.” — e cache-ul de
embeddings funcționând.

### Scenarii de testat

**a) Conversație simplă + token/cost tracking**
Scrie orice întrebare (ex. „Ce este complexitatea O(n log n)?”). După răspuns
trebuie să vezi:
```
Token Usage Summary:
Nr. total tokens in user input: ...
Input token total price: ...
...
```
Verifică vizual că prețurile folosesc 2.0 / 10.0 per milion (nu 30/70).

**b) RAG chiar aduce context relevant**
Întreabă ceva specific din `knowledge/facts/algorithm_complexity.md` (ex. „Cât
costă un lookup într-un dict?”). Dacă vrei să vezi ce chunk-uri s-au găsit, pune
temporar `DEBUG = True` în `config.py` — o să vezi în consolă
`Found N relevant chunks for the question: ...`. Pune-l înapoi pe `False` după.

**c) Tool calling**
Cere ceva ce declanșează un tool, ex.: „Ce dată e azi?” (tool `current_datetime`)
sau „Caută pe web ce e PEP 8” (tool `web_search`). Trebuie să răspundă cu
informație reală, nu inventată.

**d) Sessions — save/load**

```
You: Numele meu este Cristian.
You: save test1
You: exit
```

Repornește:

```powershell
python main.py
```

La prompt-ul „Continui conversația anterioară? [y/n]:” răspunde `n` (ca să
pornești curat), apoi:

```
You: load test1
You: Cum mă cheamă?
```

Trebuie să răspundă „Cristian” — dovadă că istoricul s-a reîncărcat corect.
Verifică și că a apărut fișierul:

```powershell
dir sessions
```

Trebuie să vezi `test1.json` și `cli_default.json` (cel din urmă se creează la
`exit` din prima rulare).

**e) Compresia de context (2.4)** — testul „greu”, dar cel mai important de arătat

În `config.py`, schimbă temporar:
```python
MAX_CONTEXT_TOKENS = 800
```
Pornește `main.py`, poartă 4-5 schimburi (primul: „Mă cheamă Ana și studiez la
FMI”), apoi întreabă „Cum mă cheamă și unde studiez?”. Trebuie să răspundă corect
DUPĂ ce istoricul s-a comprimat pe la mijloc (poți vedea în system messages
adăugate un mesaj „Summary of the earlier conversation: ...” dacă adaugi temporar
un `print(context.messages)` înainte de `agent.process_message`). Revino la
`MAX_CONTEXT_TOKENS = 4096` după test.

**f) Fallback-uri (2.1/2.2)**
- Oprește Ollama și pune o întrebare → trebuie mesaj clar „Semantic search
  skipped: ...” + agentul răspunde din cunoștințe generale, nu crapă.
- Setează temporar `$env:CHATGPT_API_KEY = "gresita"` și pune o întrebare →
  trebuie mesaj „The model rejected the API key...”, nu traceback.

---

## 2. Testarea backend-ului `api.py`

### 2.1 Pornire

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

Lasă fereastra asta deschisă (serverul rulează în foreground). Deschide un al
doilea terminal PowerShell pentru comenzile de mai jos (nu uita să activezi din
nou `my_env` acolo dacă vrei `curl`/`python`, deși `curl.exe` nativ merge oricum).

### 2.2 `GET /v1/models`

```powershell
curl http://127.0.0.1:8000/v1/models
```

Așteptat: `{"object":"list","data":[{"id":"gem-agent",...}]}`.

### 2.3 `POST /v1/chat/completions` — non-streaming

```powershell
curl -X POST http://127.0.0.1:8000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "x-user-id: alice" `
  -d '{\"model\":\"gem-agent\",\"messages\":[{\"role\":\"user\",\"content\":\"Ma numesc Alice.\"}]}'
```

Așteptat: JSON cu `choices[0].message.content` — un răspuns din persona Gem.

### 2.4 Multi-user — testul important

```powershell
curl -X POST http://127.0.0.1:8000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "x-user-id: bob" `
  -d '{\"model\":\"gem-agent\",\"messages\":[{\"role\":\"user\",\"content\":\"Cum ma cheama?\"}]}'
```

`bob` NU trebuie să știe de Alice (agent separat, context separat). Apoi:

```powershell
curl -X POST http://127.0.0.1:8000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "x-user-id: alice" `
  -d '{\"model\":\"gem-agent\",\"messages\":[{\"role\":\"user\",\"content\":\"Cum ma cheama?\"}]}'
```

`alice` trebuie să răspundă „Alice” — dovadă că istoricul ei a persistat între
cele două request-uri. Verifică și pe disc:

```powershell
dir sessions
```

Trebuie să vezi `alice.json` și `bob.json`.

### 2.5 Streaming

```powershell
curl -X POST http://127.0.0.1:8000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "x-user-id: alice" `
  -d '{\"model\":\"gem-agent\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"Salut\"}]}'
```

Așteptat: linii `data: {...}` urmate de `data: [DONE]`.

Oprește serverul cu `Ctrl+C` în terminalul unde rulează `uvicorn` (sau lasă-l pornit
și continuă direct cu secțiunea 3 — interfața web de mai jos folosește exact același
server).

---

## 3. Interfața web custom — test manual

Nu mai există un al doilea proces de instalat: `api.py` servește direct și API-ul, și
pagina (`static/index.html`, `style.css`, `app.js`).

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

Deschide `http://127.0.0.1:8000/` în browser:

1. La prima încărcare apare un prompt pentru nume — introdu unul (ex. „alice”) și
   apasă „Start chatting”.
2. Trimite un mesaj și confirmă că răspunsul apare **treptat, cuvânt cu cuvânt**
   (efectul de „typing”), nu dintr-o dată.
3. Deschide un browser în modul incognito (sau alt browser), mergi la aceeași adresă,
   introdu un nume DIFERIT (ex. „bob”), și întreabă „Cum mă cheamă?” — nu trebuie să
   știe nimic despre alice.
4. Revino la fereastra lui alice, întreabă din nou ceva ce i-ai spus mai devreme —
   trebuie să răspundă corect (istoricul ei a persistat).
5. Verifică pe disc:
   ```powershell
   dir sessions
   ```
   Trebuie să vezi `alice.json` și `bob.json`.
6. Oprește `uvicorn` (`Ctrl+C`) și repornește-l — reîncarcă pagina, aceleași nume,
   confirmă că istoricul fiecăruia s-a reîncărcat din `sessions/` (server-ul nu uită
   nimic la restart).

**Observație**: la refresh de pagină (F5), fereastra de chat se golește vizual, dar
serverul ține minte în continuare conversația — dacă întrebi ceva legat de un mesaj
anterior imediat după refresh, tot răspunde corect. Nu e un bug; pagina pur și simplu
nu reîncarcă istoricul vechi în DOM la reload (decizie deliberată de simplitate, vezi
`README.md` §8).

---

## 4. Checklist rapid înainte de predare

```powershell
# 1. importurile merg?
python -c "import agent, conversation_context, embedding_generator, llm_client, main, config, api"

# 2. CLI pornește și răspunde?
python main.py

# 3. api.py pornește?
uvicorn api:app --host 127.0.0.1 --port 8000
```

Dacă toate trei merg fără erori și ai parcurs testele multi-user din secțiunea 2.4,
proiectul e funcțional end-to-end.

## 5. Probleme frecvente

| Simptom | Cauză probabilă | Fix |
|---|---|---|
| „The model rejected the API key” | `$env:CHATGPT_API_KEY` nesetat sau greșit | Setează-l în terminalul curent |
| „Semantic search skipped: Could not connect...” | Ollama oprit | Pornește Ollama, verifică `ollama list` |
| `ModuleNotFoundError: fastapi` | Nu ești în `my_env` activat | `my_env\Scripts\Activate.ps1` |
| `uvicorn` nu pornește / port ocupat | Alt proces pe 8000 | `uvicorn api:app --port 8001` și deschide `http://127.0.0.1:8001/` |
| Sessions nu se salvează | Rulezi din alt folder decât `lab_5_skel` | `cd` în `lab5/lab_5_skel` înainte de a porni |
| Pagina din browser e goală / 404 | `static/` nu e lângă `api.py`, sau accesezi alt port | Confirmă `dir static` din `lab_5_skel` și că adresa din browser e cea unde ai pornit `uvicorn` |
