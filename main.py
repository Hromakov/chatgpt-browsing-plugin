import json
import os
import quart
import quart_cors
from quart import jsonify, Response
from quart import request
import httpx
from bs4 import BeautifulSoup

# Note: Setting CORS to allow chat.openapi.com is required for ChatGPT to access your plugin
app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

_SERVICE_AUTH_KEY = os.environ.get("_SERVICE_AUTH_KEY")



def assert_auth_header(req):
    assert req.headers.get(
        "Authorization", None) == f"Bearer {_SERVICE_AUTH_KEY}"



async def fetch_url(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

def filter_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

@app.route('/callURL', methods=['GET'])
async def callURL():
    url = quart.request.args.get('url', None)
    if not url:
        return quart.Response(response='Missing URL parameter', status=400)
    assert_auth_header(quart.request)
    raw_html = await fetch_url(url)
    filtered_html = filter_html(raw_html)
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