/* ─── THEME ───────────────────────────── */
function toggleTheme() {
    const html = document.documentElement;
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcons(next);
}

function updateThemeIcons(theme) {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
}

(function () {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    document.addEventListener('DOMContentLoaded', () => updateThemeIcons(saved));
})();

/* ─── HAMBURGER NAV ───────────────────── */
function toggleDrawer() {
    const drawer = document.getElementById('navDrawer');
    if (drawer) drawer.classList.toggle('open');
}

function closeDrawer() {
    const drawer = document.getElementById('navDrawer');
    if (drawer) drawer.classList.remove('open');
}

document.addEventListener('click', function (e) {
    const drawer = document.getElementById('navDrawer');
    const hamburger = document.querySelector('.nav-hamburger');
    if (drawer && drawer.classList.contains('open')) {
        if (!drawer.contains(e.target) && hamburger && !hamburger.contains(e.target)) {
            drawer.classList.remove('open');
        }
    }
});

/* ─── TASK TOGGLE ─────────────────────── */
function toggleTask(taskId, row) {
    fetch(`/task/${taskId}/toggle`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            row.classList.toggle('done', data.completed);
            const icon = row.querySelector('.task-check');
            if (icon) icon.textContent = data.completed ? '✅' : '⬜';

            const bar   = document.querySelector('.progress-bar');
            const label = document.querySelector('.progress-value');
            if (bar)   bar.style.width    = data.progress + '%';
            if (label) label.textContent  = data.progress + '%';
        });
}

/* ─── SPINNER ─────────────────────────── */
function showSpinner(btn) {
    const text = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    if (text) text.style.display = 'none';
    if (spinner) spinner.style.display = 'block';
    btn.disabled = true;
}

/* ─── FLASH AUTO-HIDE ─────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.flash').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 3500);
    });
});