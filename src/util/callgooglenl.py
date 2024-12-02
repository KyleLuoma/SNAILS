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

# https://developers.generativeai.google/api

import google.generativeai as genai

from vertexai.language_models import CodeGenerationModel
# https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.language_models.CodeGenerationModel
from google.generativeai.types import generation_types

import json

from google.cloud import aiplatform

aiplatform.init(project='nl-to-sql-model-eval')

pilb_prompt = """
For the database described next, provide only a sql query. do not include any text that is not valid SQL.
#
#Database: PacificIslandLandbirds
#
#MS SQL tables, with their properties:
#
#sysdiagrams(name nvarchar,principal_id int,diagram_id int,version int,definition varbinary)
#~TMPCLP650861(Habitat_ID nvarchar,Event_ID nvarchar,Canopy_Cover nvarchar,Canopy_Height int,Canopy_Comp nvarchar,Understory_Comp nvarchar,Noted_Canopy_Spp_Common nvarchar,Noted_Canopy_Spp_Scientific nvarchar)
#tbl_Db_Meta(DB_Meta_ID nvarchar,Update_Date datetime2,Update_Description nvarchar,Update_Comments nvarchar,Updated_By nvarchar,Ceritified_Data_Update bit,SSMA_TimeStamp timestamp)
#tbl_Density(Density_ID nvarchar,Event_ID nvarchar,Half_meter int,One_meter int,One_half_meter int,Two_meter int)
#tbl_Detections(Detection_ID nvarchar,Observation_ID nvarchar,Distance int,Detection int,Sort_Order int)
#tbl_Event_Details(Event_Details_ID nvarchar,Event_ID nvarchar,Cloud int,Rain int,Wind int,Gust int,P1 float,P2 float,P3 float,P4 float,P5 float,P6 float,P7 float,P8 float,P9 float,P10 float,SSMA_TimeStamp timestamp)
#tbl_Events(Event_ID nvarchar,Station_ID nvarchar,Protocol_Name nvarchar,Start_Date datetime2,Start_Time datetime2,End_Time datetime2,Repeat_Sample bit,Habitat_Date datetime2,Event_Notes nvarchar,Entered_by nvarchar,Entered_date datetime2,Updated_by nvarchar,Updated_date datetime2,Verified bit,Verified_by nvarchar,Verified_date datetime2,Certified bit,Certified_by nvarchar,Certified_date datetime2,QA_notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Habitat(Habitat_ID nvarchar,Event_ID nvarchar,Canopy_Cover nvarchar,Canopy_Height int,Canopy_Comp nvarchar,Understory_Comp nvarchar,Noted_Canopy_Spp_Common nvarchar,Noted_Canopy_Spp_Scientific nvarchar)
#tbl_Locations(Location_ID nvarchar,Site_ID nvarchar,Island nvarchar,Loc_Name nvarchar,Updated_Date datetime2,Loc_Notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Observations(Observation_ID nvarchar,Event_ID nvarchar,Species_ID nvarchar,Sort_Order int)
#tbl_Plot(Plot_ID nvarchar,Station_ID nvarchar,Slope int,Slope_Var nvarchar,Aspect int,Aspect_Var nvarchar,Topo_Position nvarchar,Paved int,Unpaved int,Stream int,Pool int)
#tbl_Sites(Site_ID nvarchar,Unit_Code nvarchar,Site_Name nvarchar,Site_Desc nvarchar,Site_Notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Stations(Station_ID nvarchar,Transect_ID nvarchar,Station nvarchar,Lat_final float,Lat_Dir nvarchar,Long_final float,Long_Dir nvarchar,Geo_Datum nvarchar,In_protocol nvarchar,Updated_date datetime2,Updated_by nvarchar,Updated_notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Stations_Updates(Update_ID nvarchar,Station_ID nvarchar,Previous_Lat float,Previous_Long float,Updated_date datetime2,Updated_by nvarchar,Updated_notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Stations_UTMs(Station_ID nvarchar,X_orig float,Y_orig float,X_final float,Y_final float,Coord_upd bit,Coord_Units nvarchar,Coord_Syst nvarchar,UTM_Zone nvarchar,Datum nvarchar,Est_H_Error real,Acc_Notes nvarchar,In_protocol nvarchar,Updated_date datetime2,Updated_by nvarchar,Updated_notes nvarchar,SSMA_TimeStamp timestamp)
#tbl_Transect(Transect_ID nvarchar,Location_ID nvarchar,Transect nvarchar,Transect_Type nvarchar,Updated_date datetime2,Updated_by nvarchar,Updated_Notes nvarchar,SSMA_TimeStamp timestamp)
#tlu_Contacts(Contact_ID nvarchar,Last_Name nvarchar,First_Name nvarchar,Middle_Init nvarchar,Obs_Code nvarchar,Organization nvarchar,Position_Title nvarchar,Address_Type nvarchar,Address nvarchar,Address2 nvarchar,City nvarchar,State_Code nvarchar,Zip_Code nvarchar,Country nvarchar,Email_Address nvarchar,Work_Phone nvarchar,Work_Extension nvarchar,Contact_Notes nvarchar,SSMA_TimeStamp timestamp)
#tlu_Enumerations(Enum_Code nvarchar,Enum_Description nvarchar,Enum_Group nvarchar,Sort_Order smallint,SSMA_TimeStamp timestamp)
#tlu_Species(Species_ID nvarchar,Family nvarchar,Scientific_Name nvarchar,Common_Name nvarchar,Species_Code nvarchar,Source nvarchar,Origin nvarchar,Status nvarchar,T&E_Status nvarchar,Habitat nvarchar,BNA_Account nvarchar,TSN int)
#xref_Event_Contacts(Event_ID nvarchar,Contact_ID nvarchar,Contact_Role nvarchar)
#xref_Species_Alternate_Names(Species_ID nvarchar,Alternate_Name nvarchar,Alternate_Type nvarchar,Update_Date datetime2,Update_By nvarchar,Update_Notes nvarchar)
#
### a sql query to answer the question: how many different types of birds are there?
"""

def call_vertex(
        prompt: str,
        model: str = "gemini-1.5-pro-latest"
) -> str:
    try:
        vertex_info_file = open(".local/vertex.json")
        vertex_info = json.loads(vertex_info_file.read())
        vertex_info_file.close()
    except FileNotFoundError as e:
        print(e)
        print("Follow instructions in ./.local/README.txt to create the required vertex.json in the .local folder.")
        raise e
    
    genai.configure(api_key=vertex_info["api_key"])

    generation_config = {
        "temperature": vertex_info["temperature"],
        "top_p": vertex_info["top_p"],
        "top_k": vertex_info["top_k"],
        "max_output_tokens": vertex_info["max_tokens"],
    }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                generation_config=generation_config,
                                safety_settings=safety_settings)

    convo = model.start_chat(history=[])
    try:
        convo.send_message(prompt)
    except generation_types.StopCandidateException as e:
        print(e)
        if hasattr(e, 'message'):
            return e.message
        else:
            return "Encountered exception without a message attribute."
    return convo.last.text


def call_google_palm(
        prompt,
        max_attempts = 10,
        model = 'text-bison',
        max_tokens = 800,
        verbose = True
) -> str:
    
    palm_info_file = open('.local/googlepalm.json')
    palm_info = json.loads(palm_info_file.read())
    palm_info_file.close()

    genai.configure(api_key = palm_info['api_key'])
    result = genai.generate_text(
        prompt=prompt,
        model=model,
        temperature=palm_info['temperature'],
        max_output_tokens=max_tokens,
        top_p=palm_info['top_p'],
        stop_sequences=['#', '--', ';']
        )
    return result.result.replace("```sql", "").strip()

def call_codey(
        prompt,
        max_attempts = 10,
        model = 'code-bison-32k',
        max_tokens = 800,
        verbose = True
) -> str:
    try:
        codey_info_file = open(".local/codey.json")
        codey_info = json.loads(codey_info_file.read())
        codey_info_file.close()
    except FileNotFoundError as e:
        print(e)
        print("Follow instructions in ./.local/README.txt to create the required openai.json in the .local folder.")
        raise e

    parameters = {
        "temperature": codey_info['temperature'],
        "max_output_tokens": max_tokens,
    }

    code_generation_model = CodeGenerationModel.from_pretrained(model)
    response = code_generation_model.predict(
        prefix=prompt, **parameters
    )

    if verbose:
        print(f"Response from {model} Model: {response.text}")

    return response.text.replace("```sql", "").replace("```", "").strip()


if __name__ == "__main__":
    prompt = "Write a sql query to get sales revenue by customer on a canonical customer database."
    # text = call_google_palm(
    #     "Write a sql query to get sales revenue by customer on a canonical customer database."
    # )
    text = call_vertex(pilb_prompt)
    print(text)