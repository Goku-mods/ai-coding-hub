const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const userId = tg?.initDataUnsafe?.user?.id || 0;
const $ = id => document.getElementById(id);

document.querySelectorAll(".tab").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
    document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));
    btn.classList.add("active");
    $(btn.dataset.page).classList.add("active");
  };
});

function msg(el, text, cls="") {
  el.className = cls;
  el.textContent = text;
}

async function refreshKey() {
  if (!userId) return;
  const r = await fetch(`/api/key-status/${userId}`);
  const d = await r.json();
  if (d.connected) {
    msg($("apiMsg"), `✓ Connected: ${d.provider}  ${d.masked}`, "success");
    $("removeBtn").classList.remove("hidden");
  } else {
    msg($("apiMsg"), "No API connected.", "");
    $("removeBtn").classList.add("hidden");
  }
}
refreshKey();

$("connectBtn").onclick = async () => {
  const key = $("apiKey").value.trim();
  if (!userId) return msg($("apiMsg"), "Open this page from Telegram.", "error");
  if (!key) return msg($("apiMsg"), "Paste your API key first.", "error");
  msg($("apiMsg"), "⏳ Testing API...", "");
  $("connectBtn").disabled = true;
  try {
    const r = await fetch("/api/connect", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({telegram_id:userId, provider:$("provider").value, api_key:key})
    });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error(d.error || "Connection failed");
    $("apiKey").value = "";
    msg($("apiMsg"), `✓ Connected successfully: ${d.masked}`, "success");
    $("removeBtn").classList.remove("hidden");
  } catch(e) {
    msg($("apiMsg"), "✕ " + e.message, "error");
  } finally {
    $("connectBtn").disabled = false;
  }
};

$("removeBtn").onclick = async () => {
  await fetch(`/api/key/${userId}`, {method:"DELETE"});
  refreshKey();
};

$("buildBtn").onclick = async () => {
  const prompt = $("prompt").value.trim();
  if (!userId) return;
  if (!prompt) return alert("Write what you want to build.");
  $("progress").classList.remove("hidden");
  $("result").classList.add("hidden");
  $("progress").innerHTML = `<div class="success">● BUILDING</div><p>Architect → Coder → Reviewer → Debugger → Finalizer</p><div class="mono">Running multi-agent coding workflow...</div>`;
  $("buildBtn").disabled = true;
  try {
    const r = await fetch("/api/build", {
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({telegram_id:userId,prompt})
    });
    const d = await r.json();
    if (!r.ok || !d.ok) throw new Error(d.error || "Build failed");
    $("progress").innerHTML = `<div class="success">✓ BUILD COMPLETE</div><p>All coding roles finished.</p>`;
    $("result").classList.remove("hidden");
    $("result").innerHTML = `<label>FINAL OUTPUT</label><div class="mono"></div>`;
    $("result").querySelector(".mono").textContent = d.result;
  } catch(e) {
    $("progress").innerHTML = `<div class="error">✕ BUILD FAILED</div><div class="mono">${e.message}</div>`;
  } finally {
    $("buildBtn").disabled = false;
  }
};
