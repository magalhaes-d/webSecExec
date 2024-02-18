from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import time

url = 'https://web-sec-ufs.streamlit.app/'

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
browser = webdriver.Chrome(options=options)
browser.get(url)
time.sleep(6)
