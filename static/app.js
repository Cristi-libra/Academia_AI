// ===================== State =====================
let USER = localStorage.getItem("gem_user") || "";
let CONV = null;              // conversația curentă
let busy = false;
let stagedFiles = [];         // fișiere atașate, urcate + trimise la Send

const $ = (s) => document.querySelector(s);
const enc = encodeURIComponent;

const WORDS = [
    "Gândește", "Analizează", "Reflectează", "Deliberează", "Cizelează",
    "Formulează", "Chibzuiește", "Cercetează", "Conectează ideile", "Evaluează",
];

const ICON = {
    user: '<svg viewBox="0 0 24 24" class="ico"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    msg: '<svg viewBox="0 0 24 24" class="ico"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    sun: '<svg viewBox="0 0 24 24" class="ico"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/></svg>',
    moon: '<svg viewBox="0 0 24 24" class="ico"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
};

// ===================== Init =====================
window.addEventListener("DOMContentLoaded", () => {
    const theme = localStorage.getItem("gem_theme") || "dark";
    setTheme(theme);

    if (USER) startApp();

    $("#name-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const name = $("#name-input").value.trim();
        if (!name) return;
        USER = name;
        localStorage.setItem("gem_user", name);
        startApp();
    });

    $("#send-btn").addEventListener("click", sendMessage);
    $("#message-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    $("#message-input").addEventListener("input", autoGrow);

    $("#attach-btn").addEventListener("click", () => $("#file-input").click());
    $("#file-input").addEventListener("change", handleFilePick);

    $("#new-chat").addEventListener("click", newConversation);
    $("#delete-btn").addEventListener("click", deleteCurrent);
    $("#export-btn").addEventListener("click", exportCurrent);
    $("#import-btn").addEventListener("click", () => $("#import-input").click());
    $("#import-input").addEventListener("change", importConversation);
    $("#switch-btn").addEventListener("click", switchUser);
    $("#theme-btn").addEventListener("click", toggleTheme);
    $("#menu-btn").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
});

// ===================== App start =====================
async function startApp() {
    $("#name-overlay").classList.add("hidden");
    $("#app").classList.remove("hidden");
    $("#user-name").textContent = USER;
    $("#message-input").focus();

    const convs = await loadConversations();
    if (convs.length) selectConversation(convs[0].id, convs[0].title);
    else newConversation();
}

function switchUser() {
    $("#app").classList.add("hidden");
    $("#name-overlay").classList.remove("hidden");
    $("#name-input").value = "";
    $("#name-input").focus();
}

// ===================== Conversations =====================
async function loadConversations() {
    try {
        const res = await fetch(`/conversations/${enc(USER)}`);
        const data = await res.json();
        renderConvList(data.conversations || []);
        return data.conversations || [];
    } catch (e) { return []; }
}

function renderConvList(items) {
    const list = $("#conv-list");
    if (!items.length) { list.innerHTML = '<div class="conv-empty muted">Nicio conversație încă.</div>'; return; }
    list.innerHTML = "";
    items.forEach((c) => {
        const el = document.createElement("button");
        el._id = c.id;
        el.type = "button";
        el.className = "conv-item" + (c.id === CONV ? " active" : "");
        el.innerHTML = `${ICON.msg}<span class="ct">${escapeHtml(c.title)}</span>`;
        el.addEventListener("click", () => selectConversation(c.id, c.title));
        list.appendChild(el);
    });
}

async function newConversation() {
    const res = await fetch(`/conversations/${enc(USER)}`, { method: "POST" });
    const { id } = await res.json();
    CONV = id;
    setTitle("Conversație nouă");
    renderWelcome();
    $("#stats").textContent = "";
    renderConvListActive();
    closeSidebarMobile();
    $("#message-input").focus();
}

async function selectConversation(id, title) {
    CONV = id;
    setTitle(title || "Conversație");
    await loadHistory();
    renderConvListActive();
    closeSidebarMobile();
}

function renderConvListActive() {
    document.querySelectorAll(".conv-item").forEach((el) => {
        el.classList.toggle("active", el._id === CONV);
    });
}

async function deleteCurrent() {
    if (!CONV) return;
    if (!confirm("Ștergi această conversație definitiv?")) return;
    await fetch(`/conversations/${enc(USER)}/${enc(CONV)}`, { method: "DELETE" });
    const convs = await loadConversations();
    if (convs.length) selectConversation(convs[0].id, convs[0].title);
    else newConversation();
}

// Descarcă conversația curentă ca JSON. Lăsăm browserul să facă download-ul
// dintr-un <a> temporar: endpoint-ul trimite deja Content-Disposition.
function exportCurrent() {
    if (!CONV) return;
    const a = document.createElement("a");
    a.href = `/export/${enc(USER)}/${enc(CONV)}`;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    a.remove();
}

async function importConversation(e) {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = "";           // permite re-importul aceluiași fișier

    const body = new FormData();
    body.append("file", file);

    try {
        const res = await fetch(`/import/${enc(USER)}`, { method: "POST", body });
        const data = await res.json();
        if (data.error) { alert(data.error); return; }

        const convs = await loadConversations();
        const entry = convs.find((c) => c.id === data.id);
        selectConversation(data.id, entry && entry.title);
    } catch (err) {
        alert("Importul a eșuat: " + err.message);
    }
}

function setTitle(t) { $("#conv-title").textContent = t; }

// ===================== History =====================
async function loadHistory() {
    try {
        const res = await fetch(`/history/${enc(USER)}/${enc(CONV)}`);
        const data = await res.json();
        if (data.messages && data.messages.length) {
            $("#chat").innerHTML = "";
            data.messages.forEach((m) => addMessage(m.role, m.content));
            updateStats(data);
        } else {
            renderWelcome();
        }
        scrollDown();
    } catch (e) { renderWelcome(); }
}

function renderWelcome() {
    $("#chat").innerHTML = `
        <div class="welcome">
            <div class="gem-logo lg"><span class="gem-facet"></span></div>
            <h2>Salut! Sunt Gem.</h2>
            <p>Întreabă-mă despre programare, dă-mi cod la corectat sau încarcă un document ca să-l evaluez.</p>
        </div>`;
}

// ===================== Send + stream =====================
async function sendMessage() {
    const input = $("#message-input");
    const text = input.value.trim();
    if ((!text && !stagedFiles.length) || busy) return;

    setBusy(true);
    removeWelcome();

    // urcă fișierele atașate ÎNAINTE de mesaj (serverul le lipește de el)
    const attachedNames = stagedFiles.map((f) => f.name);
    for (const f of stagedFiles) {
        try { await uploadStaged(f); } catch (e) { /* ignorăm, mergem mai departe */ }
    }
    stagedFiles = [];
    renderStagedChips();

    let shown = text;
    if (attachedNames.length) {
        const tag = "**📎 " + attachedNames.join(", ") + "**";
        shown = text ? (tag + "\n\n" + text) : tag;
    }
    addMessage("user", shown);
    input.value = "";
    autoGrow();

    const bubble = addMessage("assistant", "");
    const avatar = bubble.previousElementSibling;   // avatarul mic de diamant
    avatar.classList.add("av-loading");             // se animă cât gândește
    const loader = makeLoader();                     // doar cuvântul rotativ
    bubble.appendChild(loader);
    scrollDown();

    let answer = "";
    let first = true;
    const stopLoading = () => { loader.remove(); avatar.classList.remove("av-loading"); };

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: USER, conv_id: CONV, message: text }),
        });
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let buf = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            const parts = buf.split("\n\n");
            buf = parts.pop();
            for (const part of parts) {
                const line = part.trim();
                if (!line.startsWith("data:")) continue;
                const p = JSON.parse(line.slice(5).trim());
                if (p.type === "thinking") {
                    bubble.insertBefore(makeThinking(p.text), loader);
                } else if (p.type === "tools") {
                    bubble.insertBefore(makeTools(p.names), loader);
                } else if (p.type === "delta") {
                    if (first) { stopLoading(); first = false; bubble.appendChild(makeContent()); }
                    answer += p.text;
                    renderContent(bubble, answer, true);
                    scrollDown();
                } else if (p.type === "done") {
                    updateStats(p);
                } else if (p.type === "error") {
                    if (first) { stopLoading(); first = false; bubble.appendChild(makeContent()); }
                    answer = p.message;
                    renderContent(bubble, answer, false);
                }
            }
        }
    } catch (e) {
        stopLoading();
        bubble.appendChild(makeContent());
        renderContent(bubble, "Nu am putut contacta serverul.", false);
    } finally {
        stopLoading();
        renderContent(bubble, answer, false);
        setBusy(false);
        scrollDown();
        input.focus();
        loadConversations();  // reîmprospătează titlul/ordinea în sidebar
    }
}

function setBusy(s) { busy = s; $("#send-btn").disabled = s; }

// ===================== Loader (unic, mic) =====================
function makeLoader() {
    const wrap = document.createElement("div");
    wrap.className = "loader";
    const lw = document.createElement("span"); lw.className = "lw";
    let wi = Math.floor(Math.random() * WORDS.length);
    lw.textContent = WORDS[wi] + "…";
    const tw = setInterval(() => { wi = (wi + 1) % WORDS.length; lw.textContent = WORDS[wi] + "…"; }, 1600);
    wrap.append(lw);
    const rm = wrap.remove.bind(wrap);
    wrap.remove = () => { clearInterval(tw); rm(); };
    return wrap;
}

// ===================== Thinking + tools =====================
function makeThinking(text) {
    const d = document.createElement("details");
    d.className = "thinking";
    d.innerHTML = `<summary>Raționamentul modelului</summary><div class="tb"></div>`;
    d.querySelector(".tb").textContent = text;
    return d;
}
function makeTools(names) {
    const row = document.createElement("div");
    row.className = "tools-row";
    names.forEach((n) => {
        const c = document.createElement("span");
        c.className = "tool-chip";
        c.textContent = n;
        row.appendChild(c);
    });
    return row;
}

// ===================== Messages =====================
function addMessage(role, content) {
    const msg = document.createElement("div");
    msg.className = "msg " + role;

    let avatar;
    if (role === "assistant") {
        avatar = document.createElement("div");
        avatar.className = "gem-logo av";
        avatar.innerHTML = '<span class="gem-facet"></span>';
    } else {
        avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.innerHTML = ICON.user;
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    msg.append(avatar, bubble);
    $("#chat").appendChild(msg);

    if (content) { bubble.appendChild(makeContent()); renderContent(bubble, content, false); }
    return bubble;
}

function makeContent() { const c = document.createElement("div"); c.className = "content"; return c; }

function renderContent(bubble, text, cursor) {
    let c = bubble.querySelector(".content");
    if (!c) { c = makeContent(); bubble.appendChild(c); }
    c.innerHTML = mdLite(text) + (cursor ? '<span class="cursor"></span>' : "");
}

function escapeHtml(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

function mdLite(text) {
    const blocks = [];
    text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        blocks.push(`<pre><code>${escapeHtml(code.replace(/\n$/, ""))}</code></pre>`);
        return `  ${blocks.length - 1}  `;
    });
    text = escapeHtml(text);
    text = text.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.split(/\n{2,}/).map((p) => "<p>" + p.replace(/\n/g, "<br>") + "</p>").join("");
    text = text.replace(/ (\d+) /g, (_, i) => blocks[i]);
    return text;
}

function removeWelcome() { const w = $(".welcome"); if (w) w.remove(); }
function scrollDown() { const c = $("#chat"); c.scrollTop = c.scrollHeight; }
function updateStats(d) {
    if (d.input_tokens === undefined) return;
    const cost = (d.total_cost || 0).toFixed(5);
    let text = `${d.input_tokens} tokeni in · ${d.output_tokens} tokeni out · $${cost}`;
    if (d.timing && d.timing.total) {
        const t = d.timing;
        text += ` · ${t.total.toFixed(1)}s (căutare ${t.retrieval.toFixed(1)}s`
              + ` · model ${t.model.toFixed(1)}s`
              + (t.tools ? ` · tool-uri ${t.tools.toFixed(1)}s` : "")
              + ")";
    }
    $("#stats").textContent = text;
}

// ===================== File attach (stil ChatGPT: pleacă cu mesajul) =========
function handleFilePick(e) {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file || busy) return;
    stagedFiles.push(file);
    renderStagedChips();
}

function renderStagedChips() {
    let bar = $("#attach-bar");
    if (!stagedFiles.length) { if (bar) bar.remove(); return; }
    if (!bar) {
        bar = document.createElement("div");
        bar.id = "attach-bar";
        bar.className = "attach-bar";
        $(".composer-inner").before(bar);
    }
    bar.innerHTML = "";
    stagedFiles.forEach((f, i) => {
        const chip = document.createElement("span");
        chip.className = "attach-chip";
        chip.innerHTML = `<svg viewBox="0 0 24 24" class="ico"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg><span>${escapeHtml(f.name)}</span><button class="x" title="Elimină">✕</button>`;
        chip.querySelector(".x").addEventListener("click", () => { stagedFiles.splice(i, 1); renderStagedChips(); });
        bar.appendChild(chip);
    });
}

async function uploadStaged(file) {
    const form = new FormData();
    form.append("user", USER);
    form.append("conv_id", CONV);
    form.append("file", file);
    await fetch("/upload", { method: "POST", body: form });
}

// ===================== UI misc =====================
function autoGrow() {
    const el = $("#message-input");
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
}
function setTheme(t) {
    document.body.dataset.theme = t;
    $("#theme-btn").innerHTML = t === "dark" ? ICON.moon : ICON.sun;
}
function toggleTheme() {
    const next = document.body.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("gem_theme", next);
    setTheme(next);
}
function closeSidebarMobile() { $(".sidebar").classList.remove("open"); }
