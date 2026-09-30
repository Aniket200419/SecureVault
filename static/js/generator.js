/* Password Generator JS Module */

document.addEventListener('DOMContentLoaded', () => {
    const lengthRange = document.getElementById('genLengthRange');
    const lengthVal = document.getElementById('genLengthVal');
    const uppercaseCb = document.getElementById('genUppercase');
    const lowercaseCb = document.getElementById('genLowercase');
    const numbersCb = document.getElementById('genNumbers');
    const symbolsCb = document.getElementById('genSymbols');
    const outputInput = document.getElementById('genOutput');
    const generateBtn = document.getElementById('genBtn');
    const copyBtn = document.getElementById('genCopyBtn');

    if (lengthRange && lengthVal) {
        lengthRange.addEventListener('input', () => {
            lengthVal.textContent = lengthRange.value;
            generateAndDisplayPassword();
        });
    }

    [uppercaseCb, lowercaseCb, numbersCb, symbolsCb].forEach(cb => {
        if (cb) {
            cb.addEventListener('change', generateAndDisplayPassword);
        }
    });

    if (generateBtn) {
        generateBtn.addEventListener('click', generateAndDisplayPassword);
    }

    if (copyBtn && outputInput) {
        copyBtn.addEventListener('click', () => {
            if (outputInput.value) {
                copyToClipboard(outputInput.value, "Generated password copied!");
            }
        });
    }

    if (outputInput) {
        // Initial generation
        generateAndDisplayPassword();
    }
});

function generateClientPassword(length, upper, lower, nums, syms) {
    const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const LOWER = 'abcdefghijklmnopqrstuvwxyz';
    const DIGITS = '0123456789';
    const SYMBOLS = '!@#$%^&*()_+-=[]{}|;:,.<>?';

    let pools = [];
    let guaranteed = [];

    if (upper) { pools.push(UPPER); guaranteed.push(getRandomChar(UPPER)); }
    if (lower) { pools.push(LOWER); guaranteed.push(getRandomChar(LOWER)); }
    if (nums) { pools.push(DIGITS); guaranteed.push(getRandomChar(DIGITS)); }
    if (syms) { pools.push(SYMBOLS); guaranteed.push(getRandomChar(SYMBOLS)); }

    if (pools.length === 0) {
        pools = [LOWER, DIGITS];
        guaranteed = [getRandomChar(LOWER), getRandomChar(DIGITS)];
    }

    const allChars = pools.join('');
    const remainingCount = length - guaranteed.length;
    let result = [...guaranteed];

    for (let i = 0; i < remainingCount; i++) {
        result.push(getRandomChar(allChars));
    }

    // Cryptographic shuffle
    for (let i = result.length - 1; i > 0; i--) {
        const j = getSecureRandomInt(i + 1);
        [result[i], result[j]] = [result[j], result[i]];
    }

    return result.join('');
}

function getRandomChar(str) {
    const idx = getSecureRandomInt(str.length);
    return str[idx];
}

function getSecureRandomInt(max) {
    const array = new Uint32Array(1);
    window.crypto.getRandomValues(array);
    return array[0] % max;
}

function generateAndDisplayPassword() {
    const lengthRange = document.getElementById('genLengthRange');
    const uppercaseCb = document.getElementById('genUppercase');
    const lowercaseCb = document.getElementById('genLowercase');
    const numbersCb = document.getElementById('genNumbers');
    const symbolsCb = document.getElementById('genSymbols');
    const outputInput = document.getElementById('genOutput');

    if (!outputInput) return;

    const length = lengthRange ? parseInt(lengthRange.value) : 16;
    const upper = uppercaseCb ? uppercaseCb.checked : true;
    const lower = lowercaseCb ? lowercaseCb.checked : true;
    const nums = numbersCb ? numbersCb.checked : true;
    const syms = symbolsCb ? symbolsCb.checked : true;

    const pwd = generateClientPassword(length, upper, lower, nums, syms);
    outputInput.value = pwd;

    updateStrengthMeter(pwd);
}

function updateStrengthMeter(password) {
    const meterFill = document.getElementById('strengthMeterFill');
    const meterLabel = document.getElementById('strengthMeterLabel');
    const scoreVal = document.getElementById('strengthScoreVal');

    const checkLength = document.getElementById('checkLength');
    const checkUpper = document.getElementById('checkUpper');
    const checkLower = document.getElementById('checkLower');
    const checkNumber = document.getElementById('checkNumber');
    const checkSpecial = document.getElementById('checkSpecial');

    if (!password) return;

    const lenOk = password.length >= 8;
    const upperOk = /[A-Z]/.test(password);
    const lowerOk = /[a-z]/.test(password);
    const numOk = /[0-9]/.test(password);
    const specOk = /[^A-Za-z0-9]/.test(password);

    if (checkLength) setCheckStatus(checkLength, lenOk);
    if (checkUpper) setCheckStatus(checkUpper, upperOk);
    if (checkLower) setCheckStatus(checkLower, lowerOk);
    if (checkNumber) setCheckStatus(checkNumber, numOk);
    if (checkSpecial) setCheckStatus(checkSpecial, specOk);

    // Calculate score
    let score = 0;
    if (password.length >= 16) score += 30;
    else if (password.length >= 12) score += 25;
    else if (password.length >= 8) score += 15;
    else score += 5;

    if (upperOk) score += 15;
    if (lowerOk) score += 15;
    if (numOk) score += 20;
    if (specOk) score += 20;

    score = Math.min(100, Math.max(0, score));

    let rating = 'Weak';
    let meterClass = 'strength-weak';

    if (score >= 80) {
        rating = 'Very Strong';
        meterClass = 'strength-very-strong';
    } else if (score >= 60) {
        rating = 'Strong';
        meterClass = 'strength-strong';
    } else if (score >= 40) {
        rating = 'Medium';
        meterClass = 'strength-medium';
    }

    if (meterFill) {
        meterFill.style.width = score + '%';
        meterFill.className = 'strength-meter-fill ' + meterClass;
    }
    if (meterLabel) meterLabel.textContent = rating;
    if (scoreVal) scoreVal.textContent = score + '%';
}

function setCheckStatus(elem, isPassed) {
    const icon = elem.querySelector('i');
    if (isPassed) {
        elem.classList.remove('text-muted', 'text-danger');
        elem.classList.add('text-success');
        if (icon) icon.className = 'fas fa-check-circle me-2';
    } else {
        elem.classList.remove('text-success');
        elem.classList.add('text-muted');
        if (icon) icon.className = 'fas fa-times-circle me-2';
    }
}
