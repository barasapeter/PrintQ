const phoneInput = document.getElementById("phone");
const otpInput = document.getElementById("otp");
const otpSection = document.getElementById("otpSection");
const statusBox = document.getElementById("status");

const sendBtn = document.getElementById("sendOtpBtn");
const verifyBtn = document.getElementById("verifyBtn");

function setStatus(msg, type = "") {
    statusBox.textContent = msg;
    statusBox.className = "status " + type;
}

function lockAll() {
    phoneInput.disabled = true;
    otpInput.disabled = true;
    sendBtn.disabled = true;
    verifyBtn.disabled = true;
}

function lockPhoneOnly() {
    phoneInput.disabled = true;
    sendBtn.disabled = true;
}

sendBtn.addEventListener("click", async () => {
    const phone = phoneInput.value.trim();

    if (!phone) {
        setStatus("Enter a valid phone number", "error");
        return;
    }

    setStatus("Sending OTP...");

    try {
        const res = await fetch("/api/v1/otp/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone })
        });

        const data = await res.json();

        if (res.ok) {
            otpSection.classList.remove("hidden");
            setStatus("OTP sent. Enter the code.", "success");
            lockPhoneOnly();
        } else {
            setStatus(data.message || "Failed to send OTP", "error");
        }

    } catch (e) {
        setStatus("Network error", "error");
    }
});

verifyBtn.addEventListener("click", async () => {
    const phone = phoneInput.value.trim();
    const otp = otpInput.value.trim();

    if (!otp) {
        setStatus("Enter OTP code", "error");
        return;
    }

    setStatus("Verifying...");

    try {
        const res = await fetch("/api/verify-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone, otp })
        });

        const data = await res.json();

        if (res.ok) {
            setStatus("Verified. Redirecting...", "success");
            lockAll();
            // window.location.href = "/dashboard";
        } else {
            setStatus(data.message || "Invalid OTP", "error");
        }

    } catch (e) {
        setStatus("Network error", "error");
    }
});