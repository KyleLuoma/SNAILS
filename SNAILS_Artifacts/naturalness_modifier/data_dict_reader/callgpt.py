import openai
import json
import time

def call_gpt(
        prompt, 
        max_attempts = 10, 
        model = "gpt-3.5-turbo-16k",
        max_tokens=800,
        verbose=True
        ):
    try_again = True
    
    f = open('.local/openai.json')
    openai_params = json.load(f)
    f.close()
    num_attempts = 0
    client = openai.OpenAI(api_key=openai_params['api_key'])
    while try_again and num_attempts < max_attempts:
        num_attempts += 1
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt}
                ],
                temperature=openai_params['temperature'],
                max_tokens=openai_params['max_tokens'],
                top_p=openai_params['top_p'],
                frequency_penalty=openai_params['frequency_penalty'],
                presence_penalty=openai_params['presence_penalty'],
                stop=["\n"]
            )
            try_again = False
        except Exception as e:
            print("Got an error, trying again...")
            print(e)
            try_again = True
            #wait for 10 seconds
            time.sleep(10)
            print("Trying again...")

    if verbose:
        print("\nGPT response:")
        for choice in response.choices:
            print(choice.message.content)
        print("\n")
    # return response["choices"][0]["message"]["content"]
    return response.choices[0].message.content