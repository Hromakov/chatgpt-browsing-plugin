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
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

def html_to_visible_text(html, start, end):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style tags
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Get the text from the remaining tags
    text = soup.get_text()
    words = text.split()
    limited_words = words[start:end]
    return ' '.join(limited_words)

@app.route('/getHumanReadableText', methods=['GET'])
async def getHumanReadableText():
    assert_auth_header(request)
  
    url = request.args.get('url', None)
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', -1))

    if not url:
        return quart.Response(response='Missing URL parameter', status=400)

    raw_html = await fetch_url(url)
    filtered_html = html_to_visible_text(raw_html, start, end)
    return quart.Response(response=filtered_html, status=200)

def html_to_list_of_links(html, start, end):
    soup = BeautifulSoup(html, 'html.parser')

  
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href is not None:
            links.append(href)
    
    #chatgpt, convert links to text here
    text = " ".join(links)
    words = text.split()
    limited_words = words[start:end]
    return ' '.join(limited_words)

@app.route('/getLinksFromPage', methods=['GET'])
async def getLinksFromPage():
    assert_auth_header(request)
  
    url = request.args.get('url', None)
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', -1))

    if not url:
        return quart.Response(response='Missing URL parameter', status=400)

    raw_html = await fetch_url(url)
    filtered_html = html_to_list_of_links(raw_html, start, end)
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
