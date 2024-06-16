import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import base64
import concurrent.futures
import time

# URL
url = "http://127.0.0.1:8000/api/deal-missing-product-link"

response = requests.get(url)

if response.status_code == 200:
    responseData = response.json()
    
    # responseData = json.dumps(responseData, indent=4, ensure_ascii=False)
    # print("Response from server:", responseData)
else:
    print("Failed to retrieve data. Status code:", response.status_code)


def get_soup(url):
    html = requests.get(url,headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'})
    soup = BeautifulSoup(html.content, "html.parser")
    
    return soup

def get_redirected_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script')

    if script_tag:
        script_content = script_tag.string
        start_index = script_content.find('var u = "') + len('var u = "')
        end_index = script_content.find('"', start_index)
        redirected_url = script_content[start_index:end_index]
        
        return get_last_url(redirected_url)
    else:
        return None
    
def get_last_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    if 'url' in query_params:
        redirected_url = query_params['url'][0]
        return redirected_url
    else:
        return url

def decode_base64(encoded_string):
    # Kiểm tra độ dài chuỗi base64 có phải là bội số của 4 hay không
    padding_needed = len(encoded_string) % 4
    if padding_needed > 0:
        # Thêm ký tự đệm ('=') để hoàn chỉnh chuỗi base64
        encoded_string += '=' * (4 - padding_needed)
    # Giải mã base64
    decoded_string = base64.b64decode(encoded_string).decode('utf-8')

    return unquote(decoded_string)
    
def get_last_url_aclick(input):
    url = input['link']
    id = input['id']

    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if 'u' in query_params:
        last_redirect_url = query_params['u'][-1]
        last_redirect_url = decode_base64(last_redirect_url)
        response = updateDealWithLink(id, last_redirect_url)

        return response

    else:
        print("No 'u' parameter found in the URL.")

def getLink(input):
    try:
        time.sleep(1)
        bing_product_link = input['link']
        id = input['id']
        # print(bing_product_link) 
        # return
        soup = get_soup(bing_product_link)
        bingProdLink = soup.find("div", id="br-prim-obo").find("a")["href"]

        if not bingProdLink == None:
            redirected_url = get_redirected_url(bingProdLink)
            if redirected_url:
                return updateDealWithLink(id, redirected_url)
            else:
                print("No redirect found.")
        else:
            return None
    except:
        print('error: Could not find')
        pass

def updateDealWithLink(idDeal, inputlink):
    try:
        url = 'http://127.0.0.1:8000/api/update-deal-missing-product-link'
        data = {
            "id": idDeal,
            "product_link": inputlink
        }
        response = requests.post(url, json=data)

        print(response.json())
    except:
        print('update: not success')
    

allLinksProductPage = []
allLinksAclick = []
for item in responseData:
    product_link = item.get('product_link')
    itemLink = {
        'id': item.get('id'),
        'link': item.get('bing_product_link')+'&setlang=en&cc=us',
    }

    if product_link == "https://www.bing.com/shop/productpage":
        allLinksProductPage.append(itemLink)
        # inputlink = getLink(itemLink)
    else:
        allLinksAclick.append(itemLink)
        # inputlink = get_last_url_aclick(itemLink)
    # break
print(json.dumps(allLinksProductPage, indent=4))

def updateDealsLinksProductPage():
    if(len(allLinksProductPage) > 0):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(getLink, allLinksProductPage)
    else:
        print(f'\nAllLinksProductPage null')

def updateDealsLinksAclick():
    if(len(allLinksAclick) > 0):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(get_last_url_aclick, allLinksAclick)
    else:
        print(f'\nAllLinksAclick null')

# updateDealsLinksProductPage()
# updateDealsLinksAclick()





    