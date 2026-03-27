"""
Login automation for the Fasal Rin portal.
Flow:
  1. Open /login page
  2. Instantly fill username & password via JavaScript
  3. Wait for user to manually enter captcha and click Login in the browser
  4. Poll for redirect to /welcome URL
  5. Immediately navigate to reconciliation page
No captcha dialog — user handles captcha directly in the browser.
"""

from utils.constants import LOGIN_URL, RECONCILIATION_URL
from automation.browser import save_session


def perform_login(page, context, profile: dict, profile_name: str,
                  captcha_callback=None, log_callback=None):
    """
    Perform portal login.
    Auto-fills username & password instantly.
    User manually enters captcha and clicks Login in the browser.
    Detects /welcome redirect and proceeds to reconciliation page.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    # ── Already logged in? Skip entirely ──
    current_url = page.url
    if "/welcome" in current_url or "/dashboard" in current_url or "/reconciliation" in current_url:
        log("Already logged in — skipping login")
        page.goto(RECONCILIATION_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        return True

    # ── Navigate to login page ──
    log("Opening login page...")
    page.goto(LOGIN_URL, wait_until="networkidle")
    page.wait_for_timeout(500)

    # Check if session cookies made us already logged in
    if "/welcome" in page.url or "/dashboard" in page.url:
        log("Session active — already logged in")
        page.goto(RECONCILIATION_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(300)
        return True

    # Server may redirect /login → /  (SPA routing issue).
    # Push /login into the browser history so the React router activates
    # the login route, then wait for the SPA to re-render.
    if "/login" not in page.url:
        log("Server redirected to homepage — triggering client-side /login route...")
        page.evaluate("""() => {
            window.history.pushState({}, '', '/login');
            window.dispatchEvent(new PopStateEvent('popstate'));
        }""")
        page.wait_for_timeout(1000)

        # If SPA routing didn't work, try a direct location change
        if "/login" not in page.url:
            page.evaluate("window.location.hash = '#/login'")
            page.wait_for_timeout(800)

    log("On login page")

    # ── Instant-fill username via JavaScript ──
    try:
        page.evaluate("""(username) => {
            const el = document.querySelector("input[name='username']")
                     || document.querySelector("input[name='userName']")
                     || document.querySelector("input[type='text']");
            if (el) {
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, username);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", profile["username"])
        log("Username filled")
    except Exception as e:
        raise Exception(f"Could not fill username: {e}")

    # ── Instant-fill password via JavaScript ──
    try:
        page.evaluate("""(password) => {
            const el = document.querySelector("input[name='password']")
                     || document.querySelector("input[type='password']");
            if (el) {
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, password);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", profile["password"])
        log("Password filled")
    except Exception as e:
        raise Exception(f"Could not fill password: {e}")

    # ── Wait for user to enter captcha + click Login manually ──
    log("Waiting for manual captcha entry & login click in browser...")

    # Poll for /welcome URL — give user up to 2 minutes
    try:
        page.wait_for_url("**/welcome**", timeout=120000)
    except Exception:
        # Check if ended up somewhere valid
        if "/welcome" not in page.url and "/dashboard" not in page.url and "/reconciliation" not in page.url:
            raise Exception(
                "Login timed out (2 min). Please enter captcha and click Login in the browser."
            )

    log("Login successful!")

    # ── Save session & navigate to reconciliation page instantly ──
    save_session(context, profile_name)
    log("Navigating to Reconciliation page...")
    page.goto(RECONCILIATION_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(300)
    log("Ready — starting discrepancy automation")
    return True
