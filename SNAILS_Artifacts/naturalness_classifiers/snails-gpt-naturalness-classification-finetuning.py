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

import tokenprocessing as tp
import openai
import pandas as pd

#ref: https://platform.openai.com/docs/guides/fine-tuning/advanced-usage

def test():
    model_name = "davinci:ft-personal:tagged-classifier-fixed-2023-07-10-23-28-14"
    identifiers = pd.read_csv("./auto-scoring/test-set.csv")
    auto_scores = []

    for row in identifiers.itertuples():
        print(row.text)
        identifier = row.text + " " + tp.make_token_tag(row.text) + " ->"
        pred = classify_identifier(identifier, model_name)
        print(identifier, pred)
        auto_scores.append(pred.strip())

    identifiers["prediction"] = auto_scores
    file_label = model_name.replace(":", "-")
    identifiers[["text", "prediction", "category"]].to_excel(f"./auto-scoring/{file_label}.xlsx")


def classify_identifier(identifier, model_name = "davinci:ft-personal-2023-06-27-19-45-02"):
    result = openai.Completion.create(
        model = model_name,
        prompt = identifier + " ->",
        max_tokens=2
    )
    return result["choices"][0]["text"]


def add_identifier_tags(csvfile):
    filename = csvfile.replace(".csv", "")
    df = pd.read_csv(csvfile)
    df['prompt_tag'] = df.apply(
        lambda row: tp.make_token_tag(row.prompt),
        axis = 1
    )
    df['new_prompt'] = df.apply(
        lambda row: row.prompt + " " + row.prompt_tag,
        axis = 1
    )
    df[['new_prompt', 'completion']].rename(
        columns = {'new_prompt': 'prompt'}
    ).to_csv(filename + "_tagged.csv", index = False)


if __name__ == "__main__":
    test()
    # add_identifier_tags("./manual-scoring/gpt-data/validation.csv")