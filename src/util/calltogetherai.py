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

from together import Together
import json

def call_togetherai(
    prompt,
    model
) -> str:
    
    model_lookup_dict = {
        "Phind-CodeLlama-34B-v2": "Phind/Phind-CodeLlama-34B-v2",
    }

    if model in model_lookup_dict.keys():
        model = model_lookup_dict[model]

    try:
        f = open(".local/togetherai.json")
        togetherai_params = json.load(f)
        f.close()
    except FileNotFoundError as e:
        print(e)
        print("Follow instructions in ./.local/README.txt to create the required togetherai.json in the .local folder.")
        raise e
    
    api_key = togetherai_params["api_key"]

    client = Together(
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=togetherai_params["temperature"],
        top_p=togetherai_params["top_p"],
        frequency_penalty=togetherai_params["frequency_penalty"],
        presence_penalty=togetherai_params["presence_penalty"],
        max_tokens=180,
        stop=["#", ";", "``` ", "```\n"]
    )
    print("DEBUG: Response object from client.chat.completion:", response)

    response_content = response.choices[0].message.content
    if "```sql" in response_content:
        response_content = response_content.split("```sql")[1]
    if "```" in response_content:
        response_content = response_content.split("```")[0]
    return response_content

if __name__ == "__main__":

    prompt = """
For the database described next, provide only a sql query. do not include any text that is not valid SQL.
#
#Database: CratersWildlifeObservations
#
#MS SQL Server tables, with their properties:
#
#Breeding Codes( Breed int, Definition nvarchar)
#Class( Class nvarchar, DataField2 nvarchar)
#Code( DataField1 nvarchar, DataField2 nvarchar)
#HABITAT CODES( Code int, Definition nvarchar)
#Invertebrate Family( Invertebrate Family nvarchar)
#Invertebrate Order( Order nvarchar)
#INVERTEBRATES( Common Name nvarchar, Genus species nvarchar, Class nvarchar, Family nvarchar, Order nvarchar, Number float, UniversalTransverseMercatorNorth float, UniversalTransverseMercatorEast float, Datum nvarchar, Location nvarchar, Habitat float, Observation Type varchar, Date datetime2, Time datetime2, Observer nvarchar, Ownership varchar, Notes nvarchar, Survey bit, SSMA_TimeStamp timestamp)
#Month( Identification int, DataField1 nvarchar)
#Paste Errors( Date datetime2, Species nvarchar, Location nvarchar, Comments nvarchar)
#Roadkill( Date datetime2, Year nvarchar, Month nvarchar, Species nvarchar, Highway Mile Marker nvarchar, Location nvarchar, number killed nvarchar, Big Game nvarchar, Comments nvarchar)
#VERTEBRATES( Species nvarchar, Common Name nvarchar, Scientific Name nvarchar, Number float, UniversalTransverseMercatorNorth float, UniversalTransverseMercatorX float, UniversalTransverseMercatorEast float, UniversalTransverseMercatorY float, Habitat float, Observation Type nvarchar, Date datetime2, Time datetime2, Observer nvarchar, Ownership nvarchar, Notes nvarchar, Breed int, Class nvarchar, Survey nvarchar, SSMA_TimeStamp timestamp)
#WILDLIFE MASTERLIST( Species nvarchar, Common Name nvarchar, Scientific Name nvarchar)
#sysdiagrams( name nvarchar, principal_id int, diagram_id int, version int, Definition varbinary)
#
### a sql query, written in the MS SQL Server dialect, to answer the question: Show the notes for gray wolf observations with Bureau of Land Management (BLM) ownership
"""

    response = call_togetherai(
        prompt=prompt,
        model="codellama/CodeLlama-34b-Instruct-hf"
    )
    print(response)