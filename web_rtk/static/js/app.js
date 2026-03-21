let countdown;
async function generateQR() {
    const user = JSON.parse(localStorage.getItem('user'));
    const res = await fetch(`/api/generate_qr/${user.id}`);
    const data = await res.json();
    const img = document.getElementById('qr-image');
    img.src = "data:image/png;base64," + data.qr;
    img.classList.remove('hidden');
    let sec = data.expires;
    clearInterval(countdown);
    countdown = setInterval(() => {
        sec--;
        document.getElementById('timer').innerText = `Действителен: ${sec}с`;
        if (sec <= 0) resetQR();
    }, 1000);
}
function resetQR() {
    clearInterval(countdown);
    const img = document.getElementById('qr-image');
    img.src = ""; img.classList.add('hidden');
    document.getElementById('timer').innerText = "QR Аннулирован";
}
document.addEventListener("visibilitychange", () => { if (document.hidden) resetQR(); });
window.onblur = () => document.body.classList.add('blur-effect');
window.onfocus = () => document.body.classList.remove('blur-effect');