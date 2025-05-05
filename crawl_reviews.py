import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed


def crawl(url):
    """상품 링크로부터 평점, 리뷰 개수, 리뷰요약을 크롤링하는 함수"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(), options=options)
        driver.get(url)
        time.sleep(3)

        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#_productTabContainer > div > ul > li:nth-child(2) > a')))
        element.click()
        time.sleep(3)
        
        try:
            rating = driver.find_element(By.XPATH, '//*[@id="REVIEW"]/div/div/div[2]/div[1]/div/div[1]/div/span').text[-5:-1]
        except:
            rating = "N/A"
        rating_count = driver.find_element(By.XPATH, '//*[@id="REVIEW"]/div/div/div[2]/div[1]/div/div[2]/div/span[2]').text
        
        
        button_selector = "#REVIEW > div > div > div._2LvIMaBiIO > div._3aC7jlfVdk > div._2-x_A_7du6.zNGbLPTR0R > div._3BcPhzshWl > div:nth-child(1) > ul li button"
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, button_selector))
        )

        buttons = driver.find_elements(By.CSS_SELECTOR, button_selector)
        reviews = [btn.text for btn in buttons]

        driver.quit()
        return rating, rating_count, reviews
    
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return "", "", ""



def crawl_parallel(product_list) -> dict:
    """각 상품들에 대한 최저가, 카테고리, 리뷰, 평점, 평점 개수를 저장하는 딕셔너리를 반환하는 함수"""
    result = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {
            executor.submit(crawl, item["link"]): item for item in product_list
        }

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            title = item["title"]
            lprice = int(item["lprice"])
            category = item["category4"]
            try:
                rating, rating_count, reviews = future.result()
                result[title] = {
                    "최저가": lprice,
                    "카테고리":category,
                    "리뷰": reviews,
                    "평점": float(rating),
                    "리뷰 개수":rating_count
                }
            except Exception as e:
                print(f"[예외 발생] {title} - {e}")
                result[title] = {
                    "최저가": lprice,
                    "카테고리":category,
                    "리뷰": "None",
                    "평점": "None",
                    "리뷰 개수":"None"
                }

    return result