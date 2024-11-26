import os.path
import pickle
import re

import selenium.webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

ID = 7387684


def load_cookies(driver, selenium_cookie_file) -> bool:
    if os.path.exists(selenium_cookie_file):
        print("Loading cookies from " + selenium_cookie_file)
        cookies = pickle.load(open(selenium_cookie_file, "rb"))

        # Enables network tracking, so we may use Network.setCookie method
        driver.execute_cdp_cmd('Network.enable', {})

        # Iterate through pickle dict and add all the cookies
        for cookie in cookies:
            print(cookie['name'], cookie['value'])
            continue
            # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
            if 'expiry' in cookie:
                cookie['expires'] = cookie['expiry']
                del cookie['expiry']

            # Set the actual cookie
            driver.execute_cdp_cmd('Network.setCookie', cookie)
        exit()
        # Disable network tracking
        driver.execute_cdp_cmd('Network.disable', {})
        print("Cookies loaded")
        return True

    print("Cookie file " + selenium_cookie_file + " does not exist.")
    return False


def login(driver: WebDriver, name: str, password: str):
    driver.get(f"{base_url}/login/")

    driver.find_element(by=By.CSS_SELECTOR, value='.login form input[name=email]').send_keys(name)
    driver.find_element(by=By.CSS_SELECTOR, value='.login form input[name=password]').send_keys(password)
    driver.find_element(by=By.CSS_SELECTOR, value='.login form button[type=submit]').click()


def patrol_action(driver: WebDriver):
    driver.get(f"{base_url}/alley/")

    try:
        time_left = re.sub("[^0-9]", "", driver.find_element(by=By.CSS_SELECTOR, value='#patrolForm .timeleft').text)
        time_left = int(time_left)
    except Exception as e:
        print(f"failed to get time left: {type(e).__name__} {e}")
        return

    try:
        driver.find_element(by=By.CSS_SELECTOR, value='#patrolChance')
        in_progress = False
    except NoSuchElementException:
        in_progress = True

    if in_progress:
        print("already patrolling")
        return
    if time_left < 10:
        print("no time")
        return

    print(in_progress, time_left)

    driver.find_element(by=By.CSS_SELECTOR, value="#alley-patrol-button").click()


if __name__ == '__main__':
    cookie_path = os.getenv('COOKIE_PATH', './data')
    base_domain = "demwybahysknfu2xe55dpl3meu0jyewv.lambda-url.eu-central-1.on.aws"
    base_url = "https://demwybahysknfu2xe55dpl3meu0jyewv.lambda-url.eu-central-1.on.aws"

    chrome_options = selenium.webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    # chrome_options.add_argument('--headless=new')

    cookie_file = f"{cookie_path}/{ID}.cookie"

    _driver = selenium.webdriver.Chrome(options=chrome_options)

    if not load_cookies(_driver, cookie_file):
        login(_driver, name="huh@skpd.dev", password=".26y.YPmfzTQW65")
    else:
        _driver.get(f"{base_url}/player/")
        with open(cookie_file, "wb") as cookie_file:
            pickle.dump(_driver.get_cookies(), cookie_file)

    patrol_action(_driver)

    input()
