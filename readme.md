This is a custom implementation of the ChatGPT browser. It's advantage over the official browsing plugin is that you can tweak it as you want.

To install, just open replit, import from github, run the replit. You have to modify the link in the ai-plugin.json and in the yaml according to your own replit link.

Needed improvements:

1. need to limit plugin output to 100k characters, which is the openai limit.
2. need to fix the bug that does not allow scraping https://platform.openai.com/docs/guides/chat/introduction
3. need to improve the scraping algorithm, so that links will be placed inside the text rather than after it.
4. need to filter out links between useful and not useful before sending them back to chatgpt.
