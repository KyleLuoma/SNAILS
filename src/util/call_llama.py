"""
Copyright 2024 Kyle Luoma

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import requests
import json
from transformers import CodeLlamaTokenizer

def call_code_llama(
        prompt: str
) -> str:
    """
    Call a Code Llama API to generate SQL queries
    API is hosted on AWS EC2 instance using VLLM

    Parameters
    ----------
    prompt : str
        Prompt to generate SQL query from

    Returns
    -------
    query : str
        Generated SQL query
    """
    f = open('.local/codellama.json')
    llama_params = json.load(f)
    f.close()

    url = llama_params['aws_url']

    prompt_lines = prompt.split("\n")
    last_line = prompt_lines[-2]

    payload = {
        "prompt": prompt,
        "max_tokens": llama_params['max_tokens'],
        "temperature": llama_params['temperature'],
        "top_p": llama_params['top_p'],
        "n": llama_params['n'],
        "frequency_penalty": llama_params['frequency_penalty'],
        "presence_penalty": llama_params['presence_penalty'],
        "stop": ["#", ";"]
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(response)
        query = response.json()['text'][0]
        query = query[:-1].strip()
        query = query.split(last_line)[1].strip()
    else:
        print(response.status_code)
        query = "Error"

    return query



if __name__ == "__main__":
    prompt = "#a sql query to show a count of cars by color.\nSELECT"
    text = call_code_llama(prompt)
    print(text)


"""
Example of codellama.json file:
{
    "max_tokens": 2048,
    "temperature": 0,
    "top_p": 1,
    "n": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "aws_url": "http://<public IPv4 address>:8000/generate"
}
"""