from pypdf import PdfReader
from collections import defaultdict
from callgpt import call_gpt
import pandas as pd
from DataDictInterpreter import *
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--database', type=str, default='SBODemoUS', help='database name')
    database_name = parser.parse_args().database

    factory = DataDictInterpreterFactory(database_name)
    interpreter = factory.get_current_interpreter()
    # interpreter = XmlDataDictInterpreter(database_name='PacificIslandLandbirds')

    while True:
        user_input = input("Enter a database identifier: ")
        if user_input == 'quit':
            break
        natural_identifier = interpreter.getNaturalIdentifier(user_input, verbose=True)
        print(natural_identifier)



def test_driver():
    interpreter = JsonDataDictInterpreter('car_1')
    # ctx = interpreter.make_zero_shot_prompt('MPD')
    # print(ctx)
    print(interpreter.index)

if __name__ == '__main__':
    # test_driver()
    main()