import ast
import os
import sys
from dotenv import load_dotenv
import requests

# load the API key
load_dotenv()
api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not api_key:
    print("ERORR: HUGGINGFACEHUB_API_TOKEN not found in .env")
    sys.exit(1)

API_URL = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# function to read multiple lines input
def readInput() -> str:
    print("Paste your Python function. Press Enter on a blank line to finish:")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)

# function to check if the function body is empty
def isEmpty(func_node):
    for node in func_node.body:
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Constant, ast.Ellipsis)):
            continue
        return False
    return True

# function to validate the input code
def validate(source_code):
    try:
        tree = ast.parse(source_code)
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if len(functions) != 1:
            return False, "Error: This tool only generates unit tests for one function."
        node = functions[0]
        if isEmpty(node):
            return False, "Error: The provided function is empty and does not require tests."
        return True, node
    except SyntaxError:
        return False, "Error: Invalid Python code."

# function to generate unit tests using the Hugging Face API
def generateTests(node):
    source = ast.unparse(node)
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [
            {
                "role": "system",
                "content": "Generate Python unittest code only. No explanation. No markdown. Cover all branches."
            },
            {
                "role": "user",
                "content": source
            }
        ],
        "max_tokens": 600,
        "temperature": 0
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error: API request failed. {e}"

# main function to execute the script
if __name__ == "__main__":
    input_data = readInput()
    if not input_data.strip():
        print("Error: No input provided.")
        sys.exit(1)

    is_valid, result = validate(input_data)
    if not is_valid:
        print(result)
        sys.exit(1)

    test_code = generateTests(result)
    print(test_code)