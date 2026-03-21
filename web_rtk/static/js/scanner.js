const html5QrCode = new Html5Qrcode("reader");
const config = { fps: 10, qrbox: 250 };

html5QrCode.start({ facingMode: "environment" }, config, (text) => {
    verify(text);
}).catch(err => {
    console.error("Ошибка камеры:", err);
    document.getElementById('reader').innerHTML = "<p style='padding:20px; color:red; font-size:12px;'>Камера недоступна (нужен HTTPS или Localhost). Пользуйтесь ручным вводом.</p>";
});

async function verify(text) {
    if (html5QrCode.getState() === 2) await html5QrCode.pause();

    const fd = new FormData();
    fd.append('qr_data', text);

    const res = await fetch('/api/verify_qr', { method: 'POST', body: fd });
    const data = await res.json();
    
    const out = document.getElementById('sc-res');
    const nextBtn = document.getElementById('next-btn');
    
    out.style.display = "block";
    nextBtn.style.display = "block";

    if (data.status === "success") {
        out.style.background = "#e6ffed";
        out.style.color = "#155724";
        out.innerHTML = `<h3>ДОСТУП РАЗРЕШЕН ✅</h3><p><b>${data.name}</b><br>${data.position}</p>`;
    } else {
        out.style.background = "#fff0f0";
        out.style.color = "#721c24";
        out.innerHTML = `<h3>ОТКАЗАНО ❌</h3><p>${data.message}</p>`;
    }
}

function next() {
    document.getElementById('sc-res').style.display = "none";
    document.getElementById('next-btn').style.display = "none";
    document.getElementById('manual-code').value = "";
    if (html5QrCode.getState() === 3) html5QrCode.resume();
}

function manualVerify() {
    const code = document.getElementById('manual-code').value;
    if (code) verify(code);
}