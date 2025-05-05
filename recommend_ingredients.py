from google import genai
from conf import config
from pymongo import MongoClient
from crawl_reviews import crawl_parallel
import os
import json




class RecommendIngredients:
    """상품 추천 분석 서비스"""
    def __init__(self):
        self.client = genai.Client(api_key = config['GOOGLE_API_KEY'])
    
    
    def mongodb(self, keyword: str) -> list:
        """식료품DB에서 입력받은 keyword를 포함하는 title을 """
        client = MongoClient(host=config["MONGODB_HOST"], port=21017, username=config["MONGODB_USERNAME"], password=config["MONGODB_PASSWORD"])
        db = client(config["MONGODB_DB_NAME"])
        collection = db['items']
        
        query = {"title": {"$regex": keyword, "$options": "i"}}
        
        projection = {
        "_id": 0, "link":0, "image":0, "hprice":0, "mallName":0, "productId":0, "productType":0, "brand":0, "maker":0, "category1":0, "category2":0, "category3":0,
        "title": 1,
        "lprice": 1,
        "category4": 1
        }
        
        results = collection.find(query, projection)
        
        return list(results)
    
    
    def recommend(self, ingredient: str, model: str = "gemini-2.0-flash-lite"):
        """입력받은 ingredient를 db에서 쿼리하고, 상품 웹페이지에서 리뷰 등 관련 정보를 크롤링하여 분석하는 함수
        Args:
            ingredient: 검색할 식재료
        """
        try:
            ingredients_list = self.mongodb(ingredient) # db에서 서치
            ingredients_dict = crawl_parallel(ingredients_list)
            ingredients_json = json.dumps(ingredients_dict, ensure_ascii=False, indent=2)
            
            prompt = (
                "다음은 여러 식재료의 가격, 평균 별점, 리뷰 요약, 원산지 정보입니다.\n"
                "각 식재료 중 어떤 항목이 더 좋은지 분석해주고, 그 이유를 간단히 설명해주세요.\n"
                "특히 소비자 평점과 리뷰 내용에 기반해 판단해 주세요.\n\n"
                f"{ingredients_json}"
            )
            
            
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt],
                config={
                    "response_mime_type": "text/plain"
                }
            )
        except Exception as e:
            print("오류:", e)
            return None
        return response.text



recommend_service = RecommendIngredients()
