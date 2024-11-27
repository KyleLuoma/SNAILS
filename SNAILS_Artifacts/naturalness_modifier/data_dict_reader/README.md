# Retrieval-Augmented Database Identifier Expander

This program employs retrieval augmented generation to expand abbreviated database identifiers.
In its current form, it is compatible with database metadata in PDF, csv, and xml formats.
There is not a specific format requirement for the documents containing the database identifiers to be expanded because we use an LLM to extract the identifiers and their meanings from the documents.

The program was created as a part of our SNAILS project, which evaluates database schemas in terms of the naturalness of their identifiers. We include metadata and prompts associated with the SNAILS benchmark database collections.

## Installation
Setup a virtual environment (recommended) and install the requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Setup for a new database
If you want to expand identifiers for a different database, you will need a single file (.csv, .pdf, or .xml) of metadata (see folders for examples). Before using the DataDictInterpreter class in a project, you must run the main.py from the command line in order to build a few-shot prompt. The program will guide you through the process of building a prompt. Once the prompt is built, it will be saved in the prompts subfolder. You will then be able to use the command line interface to expand identifiers, and use the DataDictInterpreter class in your project.

1. Drop the metadata file in the appropriate directory.
2. Update database_dict_info.json. The key is the name of the database and the value is the filename of the metadata file. Be sure to include the file extension, as that is how the program determines which interpreter class to invoke.
3. Run the program with the name of the database as the argument. For example, if you want to expand identifiers for the SNAILS benchmark database, you would run:
```bash
python3 main.py snails
```
4. If this is the first time running the program for the new database, you will encounter a command line interaction that will work with you to iteratively build a few-shot prompt. You should be prepared to provide five identifiers. Each time you provide an identifier, the program will attempt to expand the identifier. It will provide the expanded identifier, and you will tell it whether or not it is correct. This process will repeat until it has completed five identifier expansions correctly.
5. Once the prompt is built, it will be saved in the prompts subfolder. You will then be able to use the command line interface to expand identifiers.

## Use in a project
The DataDictInterpreter class is the main interface for expanding identifiers. It can be used in a project as follows:
```python
# Import the DataDictInterpreterFactory class
from data_dict_interpreter import DataDictInterpreter
# Instantiate the DataDictInterpreterFactory class with the name of the database
# this is required because the factory class needs to know which interpreter class to instantiate based on the metadata file extension (csv, pdf, or xml)
factory = DataDictInterpreterFactory(database_name)
# Instantiate the DataDictInterpreter class with the factory
interpreter = factory.get_current_interpreter()
# Call the getNaturalIdentifier method to expand an identifier
natural_identifier = interpreter.getNaturalIdentifier("foo")
```