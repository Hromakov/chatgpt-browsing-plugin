import os
import quart
import quart_cors
from quart import request
import httpx
from requests_html import HTML
from bs4 import BeautifulSoup, Comment

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
_SERVICE_AUTH_KEY = os.environ.get("_SERVICE_AUTH_KEY")

def assert_auth_header(req):
    assert req.headers.get("Authorization", None) == f"Bearer {_SERVICE_AUTH_KEY}"

async def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(url)
        return response.text

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
    return ' '.join(limited_words)

@app.route('/getContentsOfPage', methods=['GET'])
async def getContentsOfPage():
    assert_auth_header(request)

    url = request.args.get('url', None)
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', -1))

    if not url:
        return quart.Response(response='Missing URL parameter', status=400)

    raw_html = await fetch_url(url)
    filtered_html = filter_html(raw_html, start, end)

    return quart.Response(response=filtered_html, status=200)

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