from tavily import TavilyClient
import os

tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

response = tavily_client.qna_search("What's the weather like in Madrid tomorrow?")
print(response)

response = tavily_client.search("What's the weather like in Madrid tomorrow?")
print(response)

type(response)
