from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import winsound
import json
from urllib.request import Request, urlopen
import re
from datetime import datetime

# Load settings from config.json
with open("config.json", "r") as file:
    config = json.load(file)

discord_webhook_url = config["discord_webhook_url"]
normal_delay = config["normal_delay"]
error_delay = config["error_delay"]

#retailer URLs
best_buy_url = "https://www.bestbuy.com/product/switch-2-the-legend-of-zelda-40th-anniversary-edition/J7GSL57HTY"
target_url = "https://www.target.com/p/nintendo-8482-switch-2-the-legend-of-zelda-40th-anniversary-edition-console-system/-/A-1013322047?nrtv_cid=m8oxo22g8bhwy&clkid=dcb6657bN5f7111f1baead16ec9f14199&cpng=PTID3&TCID=AFL-dcb6657bN5f7111f1baead16ec9f14199-376373&afsrc=1&lnm=201333&afid=Howl&ref=tgt_adv_xasd0002"
gamestop_url = "https://www.gamestop.com/consoles-hardware/nintendo-switch-2/products/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition/451607.html?utm_source=rakutenls&utm_medium=affiliate&utm_content=IGN&utm_campaign=10&utm_id=3011275&utm_kxconfid=tebx5rmj3&cid=afl_10000087&affID=77777&sourceID=oelFIBIMgTk-kmenyuquHsRg_Ts2WZSuVA&ranMID=24348&ranEAID=oelFIBIMgTk&ranSiteID=oelFIBIMgTk-kmenyuquHsRg_Ts2WZSuVA"
walmart_url = "https://www.walmart.com/ip/Nintendo-Switch-2-The-Legend-of-Zelda-40th-Anniversary-Edition/21002656445?action=SignIn&rm=true&action=SignIn&rm=true"
nintendo_url = "https://www.nintendo.com/us/store/products/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition-121642/"
amazon_url = "https://www.amazon.com/gp/product/B0HJ6F8L6V?psc=1"

def check_retailer_once(browser, retailer_url, stock_checker):
    page = browser.new_page()

    try:
        page.goto(
            retailer_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        status = stock_checker(page)
        return status

    finally:
        page.close()

def check_best_buy_stock(page): #test to find AddToCart element exists in site elements
    purchase_component = page.locator(
        '[data-component-name="AddToCart"]'
    )

    purchase_button = purchase_component.locator("button")#test confirming element is a button

    if purchase_button.count() == 0:
        return "UNKNOWN"

    button_text = purchase_button.inner_text().strip().lower()
    button_disabled = purchase_button.is_disabled()

    if "preorder" in button_text and not button_disabled:
        return "IN STOCK"
    if "pre-order" in button_text and not button_disabled:
        return "IN STOCK"
    if "add to cart" in button_text and not button_disabled:
        return "IN STOCK"
    if "coming soon" in button_text or "unavailable" in button_text:
        return "OUT OF STOCK"
    if button_disabled:
        return "OUT OF STOCK"
    return "UNKNOWN"

def check_target_stock(page):
    page_text = page.locator("body").inner_text().lower()

    if "press and hold" in page_text:
        return "VERIFY"
    if "quick verification" in page_text:
        return "VERIFY"
    
    purchase_component = page.locator(
        '[data-test="module-product-detail-add-to-cart"]'
    )

    try:
        purchase_component.wait_for(
            state="visible",
            timeout=30000
        )
    except PlaywrightTimeoutError:
        return "UNKNOWN"

    purchase_button = purchase_component.locator("button")

    if purchase_button.count() == 0:
        return "UNKNOWN"

    button_text = purchase_button.inner_text().strip().lower()
    button_disabled = purchase_button.is_disabled()

    if "preorder" in button_text and not button_disabled:
        return "IN STOCK"
    if "add to cart" in button_text and not button_disabled:
        return "IN STOCK"
    if button_disabled:
        return "OUT OF STOCK"
    return "UNKNOWN"

def check_gamestop_stock(page):
    purchase_component = page.locator(".cart-and-ipay:visible")

    try:
        purchase_component.wait_for(
            state="visible",
            timeout=30000
        )
    except PlaywrightTimeoutError:
        return "UNKNOWN"

    purchase_buttons = purchase_component.locator("button:visible")

    if purchase_buttons.count() == 0:
        return "UNKNOWN"

    button = purchase_buttons.first

    button_text = button.inner_text().strip().lower()
    button_disabled = button.is_disabled()
    button_test_id = button.get_attribute("data-test-id")

    if "coming soon" in button_text:
        return "OUT OF STOCK"
    if button_disabled:
        return "OUT OF STOCK"
    if (
        "pre-order" in button_text
        or "preorder" in button_text
        or "add to cart" in button_text
    ) and not button_disabled:
        return "IN STOCK"

    return "UNKNOWN"

def check_walmart_stock(page):
    shipping_status = page.locator(
        '[data-seo-id="fulfillment-Shipping-intent"]'
    )
    try:
        shipping_status.wait_for(
            state="visible",
            timeout=30000
        )
    except PlaywrightTimeoutError:
        return "UNKNOWN"

    shipping_text = shipping_status.inner_text().strip().lower()
    #print("Walmart shipping status:", shipping_text)
    if "out of stock" in shipping_text:
        return "OUT OF STOCK"

    return "UNKNOWN"

def check_nintendo_stock(page):
    purchase_button = page.get_by_role(
        "button",
        name=re.compile(
            r"^(sold out|preorder|pre-order|add to cart)$",
            re.IGNORECASE
        )
    )

    try:
        purchase_button.wait_for(
            state="visible",
            timeout=30000
        )
    except PlaywrightTimeoutError:
        return "UNKNOWN"

    button_text = purchase_button.inner_text().strip().lower()
    button_disabled = purchase_button.is_disabled()

    if "sold out" in button_text:
        return "OUT OF STOCK"
    if (
        "preorder" in button_text
        or "pre-order" in button_text
        or "add to cart" in button_text
    ) and not button_disabled:
        return "IN STOCK"
    
    return "UNKNOWN"

def check_amazon_stock(page):
    expected_asin = "B0HJ6F8L6V"
    current_url = page.url.lower()
    title = page.locator('span#productTitle')

    if expected_asin.lower() not in current_url:
        print("Amazon: unexpected product URL:", page.url)
        return "UNKNOWN"
    if title.count() == 0:
        return "UNKNOWN"
    product_title = title.inner_text().strip().lower()
    if "legend of zelda" not in product_title:
        return "UNKNOWN"

    page_text = page.locator("body").inner_text().lower()

    #Detect obvious Amazon verification pages
    if (
        "enter the characters you see below" in page_text
        or "sorry, we just need to make sure you're not a robot" in page_text):
        return "VERIFY"
    
    buy_now_button = page.locator("#buy-now-button")

    if buy_now_button.count() == 0:
        return "OUT OF STOCK"

    buy_now_text = page.locator(
        '[id="submit.buy-now-announce"]'
    )
    if buy_now_text.count() == 0:
        return "UNKNOWN"

    button_text = buy_now_text.inner_text().strip().lower()
    button_disabled = buy_now_button.is_disabled()

    if (
        "pre-order now" in button_text
        or "preorder now" in button_text
        or "buy now" in button_text
    ) and not button_disabled:
        return "IN STOCK"
    if button_disabled:
        return "OUT OF STOCK"

    return "UNKNOWN"

def play_stock_alert():
    winsound.Beep(1200, 500)
    winsound.Beep(1600, 500)
    winsound.Beep(2000, 700)

def send_discord_alert(webhook_url, message):
    try:
        data = json.dumps({
            "content": message
        }).encode("utf-8")

        request = Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StockBot/1.0"
            },
            method="POST"
        )

        with urlopen(request, timeout=10) as response:
            print("Discord alert sent:", response.status)

    except Exception as error:
        print("Discord alert failed:", error)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

#Playwright Chromium task
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False)

    #retailer dictionaries
    retailers = {
        "Best Buy": {
            "url": best_buy_url,
            "checker": check_best_buy_stock,
            "check_interval": 60,
            "verify_cooldown": 600
            },
        "GameStop": {
            "url": gamestop_url,
            "checker": check_gamestop_stock,
            "check_interval": 60,
            "verify_cooldown": 600
            },
        "Walmart": {
            "url": walmart_url,
            "checker": check_walmart_stock,
            "check_interval": 60,
            "verify_cooldown": 600
            },
        "Nintendo": {
            "url": nintendo_url,
            "checker": check_nintendo_stock,
            "check_interval": 60,
            "verify_cooldown": 600
            },
        #"Amazon": {
        #    "url": amazon_url,
        #    "checker": check_amazon_stock,
        #    "check_interval": 60,
        #    "verify_cooldown": 600
        #    },
        "Target": {
            "url": target_url,
            "checker": check_target_stock,
            "check_interval": 120,
            "verify_cooldown": 600
            }        
        }

    #status dictionary
    previous_statuses = {
        retailer_name: None
        for retailer_name in retailers
    }

    next_allowed_check = {
        retailer_name: 0
        for retailer_name in retailers
    }
    
    while True:
        for retailer_name, retailer_info in retailers.items():
            current_time = time.time()
            if current_time < next_allowed_check[retailer_name]:
                continue

            try:

                status = check_retailer_once(
                   browser,
                   retailer_info["url"],
                   retailer_info["checker"]
                )
                log(f"{retailer_name}: {status}")
                previous_status = previous_statuses[retailer_name]

                if status == "VERIFY":
                    cooldown = retailer_info["verify_cooldown"]
                    log(f"{retailer_name} requires manual verification.")
                    next_allowed_check[retailer_name] = (
                        time.time() + cooldown
                    )
                elif status == "UNKNOWN":
                    log(f"Could not determine stock status for {retailer_name}")
                    cooldown = retailer_info["verify_cooldown"]
                    next_allowed_check[retailer_name] = (
                        time.time() + retailer_info["check_interval"]
                        )
                else:
                    if status != previous_status:
                        log(f"{retailer_name} stock status changed: " 
                        f"{previous_status} -> {status}")

                        if status == "IN STOCK":
                            play_stock_alert()
                            send_discord_alert(
                                discord_webhook_url,(
                                    f"Zelda Switch 2 is IN STOCK "
                                    f"at {retailer_name}!\n "
                                    f"{retailer_info['url']}"
                                )
                            )
                        previous_statuses[retailer_name] = status

                    next_allowed_check[retailer_name] = (
                        time.time() + retailer_info["check_interval"]
                    )

            except Exception as error:
               log(
                    f"{retailer_name} check failed: {error}")
               next_allowed_check[retailer_name] = (
                   time.time() + error_delay
               )

        time.sleep(10)
