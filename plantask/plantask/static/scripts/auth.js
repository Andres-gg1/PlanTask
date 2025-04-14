document.addEventListener("DOMContentLoaded", () => {
    async function checkNetwork() {
        try {
            const res = await fetch("/validate-ip", { method: "POST" });
            const { isTrusted } = await res.json();

            if (!isTrusted) {
                const modal = document.getElementById('pingModal');
                modal.classList.add('show');
                modal.setAttribute('aria-hidden', 'false');

                const pingSubmitBtn = document.getElementById("pingSubmit");
                const pingCodeInput = document.getElementById("pingCodeInput");
                const pingError = document.getElementById("pingError");

                pingCodeInput.addEventListener("input", () => {
                    pingSubmitBtn.disabled = !pingCodeInput.value.trim();
                    pingError.classList.add("d-none");
                });

                pingSubmitBtn.onclick = async () => {
                    const codeRes = await fetch("/validate-code", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: pingCodeInput.value }),
                    });

                    const { isValid } = await codeRes.json();
                    if (isValid) {
                        modal.classList.remove('show');
                        modal.setAttribute('aria-hidden', 'true');
                        document.getElementById("loginForm").dataset.pingok = "true";
                    } else {
                        pingError.classList.remove("d-none");
                    }
                };

                document.getElementById("loginForm").addEventListener("submit", function (e) {
                    if (!this.dataset.pingok) e.preventDefault();
                });
            }
        } catch (err) {
            console.error("Network check error:", err);
        }
    }

    checkNetwork();
});