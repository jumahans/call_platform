import os
import base64
import urllib.request
import tempfile
from datetime import datetime
from seleniumbase import SB

# ====== EDIT THESE ======
EMAIL    = "GBon2000@protonmail.com"
PASSWORD = "iAiDFDYR8TJ7vM"

TO       = "abuse@example.com"
CC       = ""
SUBJECT  = "Formal Abuse Report — Tech Support Scam Infrastructure"

SCAM_URL     = "https://cdn.scammer.info/original/3X/5/3/53e9afa96d671839d3cafb1eef41515506114a1d.jpeg"
SCAM_PHONE   = "8333718469"
CARRIER_NAME = "Resporg Service LLC"

# Local file path OR http(s) URL. "" to skip.
IMAGE_PATH = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/320px-PNG_transparency_demonstration_1.png"

SCREENSHOT_DIR = r"C:\Users\Pc\OneDrive\Desktop\call_platform\sent_screenshots"
# ========================

BODY = f"""To the Compliance and Legal Departments of {CARRIER_NAME} and Microsoft Corporation,

This is a formal notification that your respective infrastructures — specifically {CARRIER_NAME}'s call-routing services and Microsoft's Azure Front Door — are currently being utilized to facilitate a criminal tech support scam.

EVIDENCE OF FRAUDULENT ACTIVITY:
Scam Phone Number: {SCAM_PHONE}
Scam URL: {SCAM_URL}
Carrier / Routing Provider: {CARRIER_NAME}

LEGAL NOTICE & ESCALATION:
Comprehensive evidence of this fraud, including the technical architecture used to trap victims, has been compiled and formally submitted to the Federal Bureau of Investigation (FBI), the Federal Communications Commission (FCC), and Federal Court authorities.

By providing the telecommunications and hosting infrastructure for this scam, your companies are enabling the financial exploitation of consumers. Under federal regulations, continuing to provide service to these known malicious actors after receiving this formal evidence may constitute negligence and complicity in fraudulent activities.

DEMAND FOR IMMEDIATE ACTION:
I demand the immediate termination of the following:
- {CARRIER_NAME}: Shut down all routing, tracking, and voice services associated with the phone number listed above.
- Microsoft: Deactivate the Azure Front Door endpoint and all associated hosting resources for the malicious URL listed above.

Failure to act immediately to neutralize these fraudulent assets will result in further legal escalations and the inclusion of your company details in the formal evidence packets provided to federal prosecutors and the courts regarding this criminal enterprise.

We expect a confirmation of service termination within 24 hours.

Evidence attached below:
"""


def resolve_image(path_or_url):
    """Return a local file path. Downloads if it's a URL."""
    if path_or_url.startswith(("http://", "https://")):
        ext = os.path.splitext(path_or_url.split("?")[0])[1] or ".png"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.close()
        req = urllib.request.Request(path_or_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(tmp.name, "wb") as f:
            f.write(r.read())
        return tmp.name
    return path_or_url


def embed_image_as_base64(sb, image_path):
    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "png")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    data_url = f"data:image/{mime};base64,{b64}"
    sb.execute_script(
        """
        var editor = document.querySelector('#rooster-editor');
        editor.focus();
        var img = document.createElement('img');
        img.src = arguments[0];
        img.style.maxWidth = '100%';
        editor.appendChild(document.createElement('br'));
        editor.appendChild(img);
        """,
        data_url,
    )


with SB(uc=True, headless=False) as sb:
    sb.open("https://account.proton.me/mail")
    sb.sleep(5)

    # Login
    sb.wait_for_element_visible('#username', timeout=15)
    sb.type('#username', EMAIL)
    sb.wait_for_element_visible('input[type="password"]', timeout=15)
    sb.type('input[type="password"]', PASSWORD)
    sb.click('button[type="submit"]')
    sb.sleep(10)

    # Open compose
    sb.wait_for_element_visible('button[data-testid="sidebar:compose"]', timeout=20)
    sb.click('button[data-testid="sidebar:compose"]')
    sb.sleep(4)

    # To
    sb.wait_for_element_visible('input[data-testid="composer:to"]', timeout=15)
    sb.type('input[data-testid="composer:to"]', TO)
    sb.send_keys('input[data-testid="composer:to"]', "\t")

    # CC
    if CC:
        sb.click('button[data-testid="composer:recipients:cc-button"]')
        sb.sleep(1)
        sb.wait_for_element_visible('input[data-testid="composer:cc"]', timeout=10)
        sb.type('input[data-testid="composer:cc"]', CC)
        sb.send_keys('input[data-testid="composer:cc"]', "\t")

    # Subject
    sb.type('input[data-testid="composer:subject"]', SUBJECT)

    # Body
    sb.switch_to_frame('iframe[data-testid="rooster-iframe"]')
    sb.wait_for_element_visible('#rooster-editor', timeout=15)
    sb.click('#rooster-editor')
    sb.execute_script(
        "document.querySelector('#rooster-editor').innerHTML = "
        "arguments[0].split('\\n').map(function(l){return '<div>' + (l || '<br>') + '</div>';}).join('');",
        BODY,
    )
    if IMAGE_PATH:
        try:
            local_img = resolve_image(IMAGE_PATH)
            embed_image_as_base64(sb, local_img)
            print(f"Embedded image: {local_img}")
        except Exception as e:
            print(f"Image embed failed: {e}")
    sb.switch_to_default_content()

    # Send
    sb.click('button[data-testid="composer:send-button"]')
    sb.wait_for_element_not_visible('section[data-testid="composer-0"]', timeout=30)
    print("Email sent.")

    # Go to Sent folder
    sb.sleep(2)
    sb.click('a[data-testid="navigation-link:all-sent"]')
    sb.sleep(3)

    # Wait for list to populate, then click the message with the latest timestamp
    sb.wait_for_element_visible('div[data-testid^="message-item:"]', timeout=15)
    sb.sleep(1)
    sb.execute_script("""
        var items = Array.from(document.querySelectorAll('div[data-testid^="message-item:"]'));
        var best = null;
        var bestTime = 0;
        items.forEach(function(item) {
            var timeEl = item.querySelector('time[data-testid="item-date-simple"]');
            if (timeEl && timeEl.getAttribute('datetime')) {
                var t = new Date(timeEl.getAttribute('datetime')).getTime();
                if (t > bestTime) { bestTime = t; best = item; }
            }
        });
        if (best) { best.click(); }
        else if (items.length) { items[0].click(); }
    """)
    sb.sleep(4)  # let body and inline image render

    # Screenshot the opened sent email
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    safe_to = TO.replace("@", "_at_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"sent_{safe_to}_{timestamp}.png")
    sb.save_screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    input("Press Enter to close browser...")