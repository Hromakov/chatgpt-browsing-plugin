import os
import quart
import quart_cors
from quart import request
import httpx
from requests_html import HTML
from bs4 import BeautifulSoup, Comment
import json
from quart import Response

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
_SERVICE_AUTH_KEY = os.environ.get("_SERVICE_AUTH_KEY")
_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
_GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")  # Replace with your search engine ID

def assert_auth_header(req):
    assert req.headers.get("Authorization", None) == f"Bearer {_SERVICE_AUTH_KEY}"

async def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            response = await client.get(url)
            return response.text
        except Exception as e:
            print(f"An error occurred while fetching the URL: {e}")
            return ""
def process_google_search_response(response):
    result_items = response.get("items", [])
    shortened_results = []

    for item in result_items:
        name = item.get("title", "")
        description = item.get("snippet", "")
        url = item.get("link", "")

        shortened_result = {
            "name": name,
            "description": description,
            "url": url,
        }
        shortened_results.append(shortened_result)

    return shortened_results

# New function to perform Google searches
async def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?key={_GOOGLE_API_KEY}&cx={_GOOGLE_SEARCH_ENGINE_ID}&q={query}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            return process_google_search_response(response.json())
        except Exception as e:
            print(f"An error occurred while performing Google search: {e}")
            return {}

def filter_html(html, start, end):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style tags
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Get the text from the remaining tags
    human_readable_text = soup.get_text()

    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href is not None:
            links.append(href)

    links_text = " ".join(links)

    full_text = human_readable_text + "\n" + links_text

    words = full_text.split()
    limited_words = words[start:end]
    limited_text = ' '.join(limited_words)

    

    return limited_text


@app.route('/getContentsOfPages', methods=['POST'])
async def getContentsOfPages():
    assert_auth_header(request)

    input_data = await request.get_json()

    if not input_data or not input_data.get('urls'):
        return quart.Response(response='Missing input data', status=400)

    results = {}
    print(input_data)
    for url in input_data['urls']:
        print(url)
        #url = url_data.get('url', None)

        if not url:
            continue

        raw_html = await fetch_url(url)
        filtered_html = filter_html(raw_html, 0, -1)

        results[url] = filtered_html



    # Convert the results dictionary to a JSON string
    json_results = json.dumps(results)
    
    # Truncate the JSON string to 99000 characters
    if(len(json_results) > 99800):
      json_results = "The output was truncated to 99800, which is the maximum. Request less URLs to get full responses. " + json_results[:99000]
    
    # Return the truncated JSON string as a response
    return Response(json_results, content_type="application/json")

# New API to handle multiple Google searches
@app.route('/googleSearches', methods=['POST'])
async def googleSearches():
    assert_auth_header(request)

    input_data = await request.get_json()

    if not input_data or not input_data.get('queries'):
        return quart.Response(response='Missing input data', status=400)

    results = {}
    for query in input_data['queries']:
        search_results = await google_search(query)
        results[query] = search_results

    return quart.jsonify(results)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5002)

if __name__ == "__main__":
   main()