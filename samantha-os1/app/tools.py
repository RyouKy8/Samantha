"""
Derived from https://github.com/Chainlit/cookbook/tree/main/realtime-assistant
and https://github.com/disler/poc-realtime-ai-assistant/tree/main
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import base64
import os
import logging
import webbrowser

import chainlit as cl
import plotly
import yfinance as yf
from tavily import TavilyClient
from together import Together
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import traceback

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Scratchpad directory
scratch_pad_dir = "../scratchpad"
os.makedirs(scratch_pad_dir, exist_ok=True)

# Initialize clients
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

# Define the tools
query_stock_price_def = {
    "name": "query_stock_price",
    "description": "Queries the latest stock price information for a given stock symbol.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "The stock symbol to query (e.g., 'AAPL' for Apple Inc.)",
            },
            "period": {
                "type": "string",
                "description": "The time period for which to retrieve stock data (e.g., '1d' for one day, '1mo' for one month)",
            },
        },
        "required": ["symbol", "period"],
    },
}


async def query_stock_price_handler(symbol, period):
    """
    Queries the latest stock price information for a given stock symbol.
    """
    try:
        logger.info(f"📈 Fetching stock price for symbol: {symbol}, period: {period}")
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty:
            logger.warning(f"⚠️ No data found for symbol: {symbol}")
            return {"error": "No data found for the given symbol."}
        logger.info(f"💸 Stock data retrieved successfully for symbol: {symbol}")
        return hist.to_json()
    except Exception as e:
        logger.error(f"❌ Error querying stock price for symbol: {symbol} - {str(e)}")
        return {"error": str(e)}


query_stock_price = (query_stock_price_def, query_stock_price_handler)

draw_plotly_chart_def = {
    "name": "draw_plotly_chart",
    "description": "Draws a Plotly chart based on the provided JSON figure and displays it with an accompanying message.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to display alongside the chart",
            },
            "plotly_json_fig": {
                "type": "string",
                "description": "A JSON string representing the Plotly figure to be drawn",
            },
        },
        "required": ["message", "plotly_json_fig"],
    },
}


async def draw_plotly_chart_handler(message: str, plotly_json_fig):
    try:
        logger.info(f"🎨 Drawing Plotly chart with message: {message}")
        fig = plotly.io.from_json(plotly_json_fig)
        elements = [cl.Plotly(name="chart", figure=fig, display="inline")]
        await cl.Message(content=message, elements=elements).send()
        logger.info(f"💡 Plotly chart displayed successfully.")
    except Exception as e:
        logger.error(f"❌ Error drawing Plotly chart: {str(e)}")
        return {"error": str(e)}


draw_plotly_chart = (draw_plotly_chart_def, draw_plotly_chart_handler)

generate_image_def = {
    "name": "generate_image",
    "description": "Generates an image based on a given prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The prompt to generate an image (e.g., 'A beautiful sunset over the mountains')",
            },
        },
        "required": ["prompt"],
    },
}


class EnhancedPrompt(BaseModel):
    """
    Class for the text prompt
    """

    content: str = Field(
        ...,
        description="The enhanced text prompt to generate an image",
    )


async def generate_image_handler(prompt):
    """
    Generates an image based on a given prompt using the Together API.
    """
    try:

        logger.info(f"✨ Enhancing prompt: '{prompt}'")

        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.25,
            max_retries=2,
        )

        structured_llm = llm.with_structured_output(EnhancedPrompt)

        system_template = """
        Enhance the given prompt the best prompt engineering techniques such as providing context, specifying style, medium, lighting, and camera details if applicable. If the prompt requests a realistic style, the enhanced prompt should include the image extension .HEIC.

        # Original Prompt
        {prompt}

        # Objective
        **Enhance Prompt**: Add relevant details to the prompt, including context, description, specific visual elements, mood, and technical details. For realistic prompts, add '.HEIC' in the output specification.

        # Example
        "realistic photo of a person having a coffee" -> "photo of a person having a coffee in a cozy cafe, natural morning light, shot with a 50mm f/1.8 lens, 8425.HEIC"
        """

        prompt_template = PromptTemplate(
            input_variables=["prompt"],
            template=system_template,
        )

        chain = prompt_template | structured_llm

        # Generate the LinkedIn post
        enhanced_prompt = chain.invoke({"prompt": prompt}).content

        logger.info(f"🌄 Generating image based on prompt: '{enhanced_prompt}'")
        response = together_client.images.generate(
            prompt=prompt,
            # model="black-forest-labs/FLUX.1-schnell-Free",
            model="black-forest-labs/FLUX.1.1-pro",
            width=1024,
            height=768,
            steps=4,
            n=1,
            response_format="b64_json",
        )

        b64_image = response.data[0].b64_json
        image_data = base64.b64decode(b64_image)

        img_path = os.path.join(scratch_pad_dir, "generated_image.jpeg")
        with open(img_path, "wb") as f:
            f.write(image_data)

        logger.info(f"🖼️ Image generated and saved successfully at {img_path}")
        image = cl.Image(path=img_path, name="Generated Image", display="inline")
        await cl.Message(
            content=f"Image generated with the prompt '{enhanced_prompt}'",
            elements=[image],
        ).send()

        return "Image successfully generated"

    except Exception as e:
        logger.error(f"❌ Error generating image: {str(e)}\n{traceback.format_exc()}")
        # logger.error(f"❌ Error generating image: {str(e)}")
        return {"error": str(e)}


generate_image = (generate_image_def, generate_image_handler)

internet_search_def = {
    "name": "internet_search",
    "description": "Performs an internet search using the Tavily API.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the internet (e.g., 'What's the weather like in Madrid tomorrow?').",
            },
        },
        "required": ["query"],
    },
}


async def internet_search_handler(query):
    """
    Executes an internet search using the Tavily API and returns the result.
    """
    try:
        logger.info(f"🕵 Performing internet search for query: '{query}'")
        response = tavily_client.search(query)

        # Extracting the result for formatting
        results = response.get("results", [])
        if not results:
            await cl.Message(content=f"No results found for '{query}'.").send()
            return None

        # Formatting the results in a more readable way
        formatted_results = "\n".join(
            [
                f"{i+1}. [{result['title']}]({result['url']})\n{result['content'][:200]}..."
                for i, result in enumerate(results)
            ]
        )

        message_content = f"Search Results for '{query}':\n\n{formatted_results}"
        await cl.Message(content=message_content).send()

        logger.info(f"📏 Search results for '{query}' retrieved successfully.")
        return response["results"]
    except Exception as e:
        logger.error(f"❌ Error performing internet search: {str(e)}")
        await cl.Message(
            content=f"An error occurred while performing the search: {str(e)}"
        ).send()


internet_search = (internet_search_def, internet_search_handler)

draft_linkedin_post_def = {
    "name": "draft_linkedin_post",
    "description": "Creates a LinkedIn post draft based on a given topic or content description.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic or content description for the LinkedIn post (e.g., 'The importance of AI ethics in modern technology').",
            },
        },
        "required": ["topic"],
    },
}


class LinkedInPost(BaseModel):
    """
    LinkedIn post draft.
    """

    content: str = Field(
        ...,
        description="The drafted LinkedIn post content",
    )


async def draft_linkedin_post_handler(topic):
    """
    Creates a LinkedIn post draft based on a given topic or content description.
    """
    try:
        logger.info(f"📝 Drafting LinkedIn post on topic: '{topic}'")

        # Initialize the Groq chat model
        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.25,
            max_retries=2,
        )

        structured_llm = llm.with_structured_output(LinkedInPost)

        system_template = """
        Create an engaging LinkedIn post for a given topic incorporating relevant emojis to capture attention and convey the message effectively. 

        # Topic
        {topic}

        # Steps
        1. **Identify the main message**: Determine the core topic or idea you want to communicate in the post.
        2. **Audience Consideration**: Tailor your language and tone to fit the audience you are addressing on LinkedIn.
        3. **Incorporate Emojis**: Select emojis that complement the text and reinforce the message without overwhelming it.
        4. **Structure the Post**: Organize the content to include an engaging opening, informative content, and a clear call-to-action if applicable.
        """

        prompt_template = PromptTemplate(
            input_variables=["topic"],
            template=system_template,
        )

        chain = prompt_template | structured_llm

        # Generate the LinkedIn post
        linkedin_post = chain.invoke({"topic": topic}).content

        # Save the post to a .md file
        filepath = os.path.join(scratch_pad_dir, "linkedin_post.md")
        with open(filepath, "w") as f:
            f.write(linkedin_post)

        logger.info(f"💾 LinkedIn post saved successfully at {filepath}")

        # Send the LinkedIn post as a message in Chainlit
        await cl.Message(
            content=f"LinkedIn post about '{topic}':\n\n{linkedin_post}"
        ).send()
        logger.info("📨 LinkedIn post sent as a message.")

        return linkedin_post

    except Exception as e:
        logger.error(f"❌ Error drafting LinkedIn post: {str(e)}")
        await cl.Message(
            content=f"An error occurred while drafting the LinkedIn post: {str(e)}"
        ).send()


draft_linkedin_post = (draft_linkedin_post_def, draft_linkedin_post_handler)


create_python_file_def = {
    "name": "create_python_file",
    "description": "Creates a Python file based on a given topic or content description.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The name of the Python file to be created (e.g., 'script.py').",
            },
            "content_description": {
                "type": "string",
                "description": "The content description for the Python file (e.g., 'Generate a random number').",
            },
        },
        "required": ["filename", "topic"],
    },
}


class PythonFile(BaseModel):
    """
    Python file content.
    """

    filename: str = Field(
        ...,
        description="The name of the Python file with the extenstion .py",
    )
    content: str = Field(
        ...,
        description="The Python code to be saved in the file",
    )


async def create_python_file_handler(filename: str, content_description: str):
    """
    Creates a Python file with the provided filename based on a given topic or content description.
    """
    try:
        logger.info(f"📝 Drafting Python file that '{content_description}'")

        # Initialize the Groq chat model
        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.1,
            max_retries=2,
        )

        structured_llm = llm.with_structured_output(PythonFile)

        system_template = """
        Create a Python script for the given topic. The script should be well-commented, use best practices, and aim to be simple yet effective. 
        Include informative docstrings and comments where necessary.

        # Topic
        {content_description}

        # Requirements
        1. **Define Purpose**: Write a brief docstring explaining the purpose of the script.
        2. **Implement Logic**: Implement the logic related to the topic, keeping the script easy to understand.
        3. **Best Practices**: Follow Python best practices, such as using functions where appropriate and adding comments to clarify the code.
        """

        prompt_template = PromptTemplate(
            input_variables=["content_description"],
            template=system_template,
        )

        chain = prompt_template | structured_llm

        # Generate the Python file content
        python_file = chain.invoke({"content_description": content_description})
        content = python_file.content

        filepath = os.path.join(scratch_pad_dir, filename)
        os.makedirs(scratch_pad_dir, exist_ok=True)

        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"💾 Python file '{filename}' created successfully at {filepath}")
        await cl.Message(
            content=f"Python file '{filename}' created successfully based on the topic '{content_description}'."
        ).send()
        return f"Python file '{filename}' created successfully."

    except Exception as e:
        logger.error(f"❌ Error creating Python file: {str(e)}")
        await cl.Message(
            content=f"An error occurred while creating the Python file: {str(e)}"
        ).send()
        return f"An error occurred while creating the Python file: {str(e)}"


create_python_file = (create_python_file_def, create_python_file_handler)

execute_python_file_def = {
    "name": "execute_python_file",
    "description": "Executes a Python file in the scratchpad directory using the current Python environment.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "The name of the Python file to be executed (e.g., 'script.py').",
            },
        },
        "required": ["filename"],
    },
}


async def execute_python_file_handler(filename: str):
    """
    Executes a Python file in the scratchpad directory using the current Python environment.
    """
    try:
        filepath = os.path.join(scratch_pad_dir, filename)

        if not os.path.exists(filepath):
            error_message = (
                f"Python file '{filename}' not found in scratchpad directory."
            )
            logger.error(f"❌ {error_message}")
            await cl.Message(content=error_message).send()
            return error_message

        result = subprocess.run(
            ["python", filepath],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"✅ Successfully executed Python file '{filename}'")
            output_message = result.stdout
            await cl.Message(
                content=f"Output of '{filename}':\n\n{output_message}"
            ).send()
            return output_message
        else:
            error_message = f"Error executing Python file '{filename}': {result.stderr}"
            logger.error(f"❌ {error_message}")
            await cl.Message(content=error_message).send()
            return error_message

    except Exception as e:
        logger.error(f"❌ Error executing Python file: {str(e)}")
        await cl.Message(
            content=f"An error occurred while executing the Python file: {str(e)}"
        ).send()
        return f"An error occurred while executing the Python file: {str(e)}"


execute_python_file = (execute_python_file_def, execute_python_file_handler)

open_browser_def = {
    "name": "open_browser",
    "description": "Opens a browser tab with the best-fitting URL based on the user's prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user's prompt to determine which URL to open.",
            },
        },
        "required": ["prompt"],
    },
}


class WebUrl(BaseModel):
    """
    Web URL response.
    """

    url: str = Field(
        ...,
        description="The URL to open in the browser",
    )


async def open_browser_handler(prompt: str):
    """
    Open a browser tab with the best-fitting URL based on the user's prompt.
    """
    try:
        logger.info(f"📖 open_browser() Prompt: {prompt}")

        browser_urls = [
            "https://www.chatgpt.com",
            "https://www.tesla.com",
            "https://www.spacex.com",
        ]
        browser_urls_str = "\n".join(browser_urls)
        browser = "chrome"

        prompt_structure = f"""
        Select a browser URL from the list of browser URLs based on the user's prompt.

        # Steps:
        1. Infer the browser URL that the user wants to open from the user-prompt and the list of browser URLs.
        2. If the user-prompt is not related to the browser URLs, return an empty string.

        # Browser URLs:
        {browser_urls_str}

        # Prompt:
        {prompt}
        """

        # Initialize the Groq chat model
        llm = ChatGroq(
            model="llama3-70b-8192",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0,
            max_retries=2,
        )

        structured_llm = llm.with_structured_output(WebUrl)
        response = structured_llm.invoke(prompt_structure)

        logger.info(f"📖 open_browser() Response: {response}")

        # Open the URL if it's not empty
        if response.url:
            logger.info(f"📖 open_browser() Opening URL: {response.url}")
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, webbrowser.get(browser).open, response.url
                )
            return f"URL opened successfully in the browser: {response.url}"
        else:
            error_message = f"Error retrieving URL from the prompt: {prompt}"
            logger.error(f"❌ {error_message}")
            await cl.Message(content=error_message).send()
            return error_message

    except Exception as e:
        logger.error(f"❌ Error opening browser: {str(e)}")
        return {"status": "Error", "message": str(e)}


open_browser = (open_browser_def, open_browser_handler)

tools = [
    query_stock_price,
    draw_plotly_chart,
    generate_image,
    internet_search,
    draft_linkedin_post,
    create_python_file,
    execute_python_file,
    open_browser,
]
