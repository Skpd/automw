import os.path
import pickle
import re

import selenium.webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

ID = 7387684


def login(driver: WebDriver, name: str, password: str):
    driver.get("https://www.moswar.ru/login/")

    driver.find_element(by=By.CSS_SELECTOR, value='.login form input[name=email]').send_keys(name)
    driver.find_element(by=By.CSS_SELECTOR, value='.login form input[name=password]').send_keys(password)
    driver.find_element(by=By.CSS_SELECTOR, value='.login form button[type=submit]').click()


def patrol_action(driver: WebDriver):
    driver.get("https://www.moswar.ru/alley/")

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
    chrome_options = selenium.webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    _driver = selenium.webdriver.Chrome(options=chrome_options)
    _driver.get("https://www.moswar.ru/")

    if os.path.exists(f"{ID}.cookie"):
        with open(f"{ID}.cookie", "rb") as cookie_file:
            cookies = pickle.load(cookie_file)
            for cookie in cookies:
                _driver.add_cookie(cookie)
    else:
        login(_driver, name="huh@skpd.dev", password=".26y.YPmfzTQW65")

    _driver.get("https://www.moswar.ru/player/")
    with open(f"{ID}.cookie", "wb") as cookie_file:
        pickle.dump(_driver.get_cookies(), cookie_file)

    patrol_action(_driver)

    input()
