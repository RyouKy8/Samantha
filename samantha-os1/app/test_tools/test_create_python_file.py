import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


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
{topic}

# Requirements
1. **Define Purpose**: Write a brief docstring explaining the purpose of the script.
2. **Implement Logic**: Implement the logic related to the topic, keeping the script easy to understand.
3. **Best Practices**: Follow Python best practices, such as using functions where appropriate and adding comments to clarify the code.
"""

prompt_template = PromptTemplate(
    input_variables=["topic"],
    template=system_template,
)

chain = prompt_template | structured_llm

response = chain.invoke({"topic": "Print a random number from 500 to 1000."})

print(response.filename)
print(response.content)
