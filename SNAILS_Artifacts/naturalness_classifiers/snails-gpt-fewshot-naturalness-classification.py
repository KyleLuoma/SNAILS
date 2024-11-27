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

import pandas as pd
import callgpt

f = open('prompts/fewshot-categoryexplanations.txt')
prompt = f.read()
f.close()

validation_df = pd.read_csv('auto-scoring/test-set.csv')
results = []

for row in validation_df.itertuples():
    identifier = row.text
    replaced_prompt = prompt.replace("_IDENTIFIER_", identifier)
    response = callgpt.call_gpt(replaced_prompt, model='gpt-4')
    if response in ["N1", "N2", "N3"]:
        results.append(response)
    else:
        results.append("INVALID RESPONSE")
    print("GPT response:")

validation_df['gpt_predict'] = results
validation_df[['text', 'gpt_predict', 'category']].to_csv('auto-scoring/gpt-4-fewshot.csv', index=False)