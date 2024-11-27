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

# A GUI-based manual query evaluator that iterates through predicted and gold queries and other 
# information found in the output workbooks from the end-to-end-prototype-data-prep-and-prediction notebook.
# Uses the TKinter library for the GUI.

import pandas as pd
import json
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import messagebox
import query_profiler as qp

def separate_by_line(query) -> list:
    for c in ['\n', '\r', '\t']:
        query = query.replace(c, ' ')
    for kw in ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'LIMIT', 'JOIN']:
        query = query.replace(kw, ' \n' + kw)
        query = query.replace(kw.lower(), ' \n' + kw)
    return query

def clean(elmnt: str) -> str:
    for s in ['set()', '{', '}']:
        elmnt = elmnt.replace(s, '')
    return elmnt


def evaluate_queries_in_workbook(init_file_open_dir=None, init_filename=None) -> pd.DataFrame:
    """
    Opens a GUI window to evaluate SQL queries stored in an Excel workbook. The function allows users to load a workbook, 
    navigate through questions, manually score the queries, and save the annotations.
    Args:
        init_file_open_dir (str, optional): Initial directory to open the workbook from. Defaults to None.
        init_filename (str, optional): Initial filename of the workbook to open. Defaults to None.
    Returns:
        pd.DataFrame: The annotated workbook as a pandas DataFrame.
    """


    class DfVariable(tk.Variable):

        def __init__(self, value: pd.DataFrame = None):
            super().__init__()
            self._df = value

        def get(self):
            return self._df
        
        def set(self, value: pd.DataFrame):
            self._df = value


    # ---- Lookups ----
    tf_lookup = {1: True, 0: False, -1: "Ungraded"}

    # ---- Font styles ----
    style_query_text = ('Consolas', 12)
    style_header_text = ('Helvatical bold',14)
    style_question_text = ('Halvatical bold', 12)

    # ---- Command functions ----
    
    def handle_save_workbook():
        save_notes()
        workbook = workbook_var.get()
        workbook.reset_index(inplace=True)
        saveas_filename = fd.asksaveasfilename(
            confirmoverwrite=True,
            defaultextension='xlsx',
            title='Save annotations',
            initialdir=file_save_dir.get(),
            initialfile=filename.get()
        )
        print(saveas_filename)
        if len(saveas_filename) > 0: 
            workbook.to_excel(saveas_filename)
        modified_var.set(False)


    def handle_load_workbook():
        proceed = True
        if modified_var.get():
            proceed = messagebox.askokcancel(
                title="Unsaved data", 
                message="Modifactions made since last save will be lost if you continue. Do you wish to proceed?",
                )
        if not proceed:
            return
        new_filename = fd.askopenfilename(
            defaultextension=".xlsx",
            initialdir=file_open_dir.get()
        )
        print(new_filename.split("/")[-1])
        workbook = load_workbook(new_filename)
        if workbook.shape[0] > 0:
            workbook_var.set(workbook)
            highest_q_num.set(workbook_var.get().shape[0])
            highest_q_num.set(max(workbook.index))
            lowest_q_num.set(min(workbook.index))
            question_num_lbl['text'] = f'Question Num: {lowest_q_num.get()}'
            # handle_next_question()
            load_new_question(lowest_q_num.get())
            modified_var.set(False)
            filename.set(new_filename.split("/")[-1])


    def load_new_question(nx_q):
        workbook = workbook_var.get()
        num_ungraded_var.set(workbook_var.get().query('manual_match == -1').shape[0])
        question_num_lbl['text'] = f'Question Num: {nx_q}'
        question_lbl['text'] = workbook.loc[nx_q]['question']
        gold_query['text'] = separate_by_line(workbook.loc[nx_q]['query_gold'])
        pred_query['text'] = separate_by_line(workbook.loc[nx_q]['query_predicted'])
        res_match_lbl['text'] = f"Result Set Match: {tf_lookup[workbook.loc[nx_q]['result_set_match']]}"
        recall_score_lbl['text'] = f"Recall: {workbook.loc[nx_q]['recall']}" 
        precision_score_lbl['text'] = f"Precision: {workbook.loc[nx_q]['precision']}" 
        f1_score_lbl['text'] = f"F1: {workbook.loc[nx_q]['f1']}"
        syntax_error_ct_lbl['text'] = f"Syntax Errors: {workbook.loc[nx_q]['syntax_error_count']}"
        halucination_ct_lbl['text'] = f"Hallucinations: {workbook.loc[nx_q]['hallucination_count']}"
        man_match_var.set(int(workbook.loc[nx_q]['manual_match']))
        schema_matches = (
            "\n   Tables: " + clean(workbook.loc[nx_q]['matching_tables']) 
            +"\n   Columns: " + clean(workbook.loc[nx_q]['matching_columns'])
            )
        matching_lab['text'] = f"-- Schema matches -- {schema_matches}"
        schema_missing = (
            "\n   Tables: " + clean(workbook.loc[nx_q]['missing_tables']) 
            +"\n   Columns: " + clean(workbook.loc[nx_q]['missing_columns'])
            )
        missing_lab['text'] = f"-- Schema missing -- {schema_missing}"
        schema_extra = (
            "\n   Tables: " + clean(workbook.loc[nx_q]['extra_tables'])
            +"\n   Columns: " + clean(workbook.loc[nx_q]['extra_columns'])
            )
        extra_lab['text'] = f"-- Schema extras -- {schema_extra}"
        man_match_txt.delete('0.0', tk.END)
        man_match_txt.insert('0.0', workbook.loc[nx_q]['review_notes'])
        num_ungraded_lab['text'] = f"Remaining Ungraded: {num_ungraded_var.get()}"



    def handle_next_question():
        save_notes()
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        if cur_q < highest_q_num.get():
            nx_q = cur_q + 1
        else: 
            nx_q = lowest_q_num.get()
        load_new_question(nx_q)
        

    def handle_prev_question():
        save_notes()
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        if cur_q > lowest_q_num.get():
            nx_q = cur_q - 1
        else: 
            nx_q = highest_q_num.get()
        load_new_question(nx_q)


    def handle_next_ungraded_question():
        save_notes()
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        ungraded = workbook_var.get().query("manual_match == -1")
        q_nums = ungraded.index.to_list()
        if len(q_nums) == 0:
            return
        for q in q_nums:
            if q > cur_q:
                load_new_question(q)
                return
        load_new_question(q_nums[0])


    def handle_log_match_and_next_ungraded():
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        workbook_var.get().at[cur_q, 'manual_match'] = 1
        modified_var.set(True)
        handle_next_ungraded_question()


    def handle_manual_scoring():
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        workbook_var.get().at[cur_q, 'manual_match'] = man_match_var.get()
        modified_var.set(True)


    def save_notes():
        cur_q = int(question_num_lbl['text'].split(':')[1].strip())
        if cur_q == 0:
            return
        if man_match_txt.get('0.0', tk.END).strip() != workbook_var.get().loc[cur_q]['review_notes'].strip():
            workbook_var.get().at[cur_q, 'review_notes'] = man_match_txt.get('0.0', tk.END).strip()
            modified_var.set(True)
        

    def load_workbook(filepath_name: str) -> pd.DataFrame:
        try:
            workbook = pd.read_excel(filepath_name, engine='openpyxl', sheet_name='Sheet1')
            workbook.set_index('number', inplace=True)
            if 'manual_match' not in workbook.columns:
                workbook['manual_match'] = workbook.apply(
                    lambda row: {
                        0: 0,
                        1: -1
                    }[row.result_set_match],
                    axis = 1
                )

            if 'review_notes' not in workbook.columns:
                workbook['review_notes'] = ''
            else:
                workbook['review_notes'] = workbook.review_notes.fillna('')
            return workbook
        except:
            messagebox.showerror(title="File load error", message=f"Error while loading {filepath_name}")
            return pd.DataFrame()

    # ---- WINDOW -----
    window = tk.Tk(
        screenName='Query Evaluator'
    )
    for i in range(2):
        window.columnconfigure(i, weight=1, minsize=500)
        window.rowconfigure(i, weight=0, minsize=20)

    # ---- LOAD AND SAVE ----
    if init_file_open_dir != None and init_filename != None:
        file_open_dir = tk.StringVar(value=init_file_open_dir)
        filename = tk.StringVar(value=init_filename)
    else:
        file_open_dir = tk.StringVar(value="./nl-to-sql_performance_annotations/pending_evaluation/")
        filename = tk.StringVar(value='example.xlsx')
    file_save_dir = tk.StringVar(value="./nl-to-sql_performance_annotations/")
    workbook = load_workbook(f"{file_open_dir.get()}{filename.get()}")
    workbook_var = DfVariable(value=workbook)
    highest_q_num = tk.IntVar(value = max(workbook.index))
    lowest_q_num = tk.IntVar(value = min(workbook.index))


    # ---- NL Question Frame and Lables ----
    question_frm = tk.Frame(
        master=window
    )
    question_num_lbl = tk.Label(
        master=question_frm, 
        text='Question Num: 0',
        justify='left',
        font=style_header_text
        )
    question_num_lbl.grid(row=0, column=0, sticky="nw")
    question_lbl = tk.Label(
        master=question_frm, 
        text='Press the LOAD button above to open a workbook for manual evaluation.',
        wraplength=600,
        justify='left',
        font=style_question_text
        )
    question_lbl.grid(row=1, column=0, sticky="nw")
    question_frm.grid(row=1, column=0, sticky="nw")

    # ---- Auto scoring data ----
    scores_frm = tk.Frame(
        master=window
    )
    res_match_lbl = tk.Label(
        master=scores_frm,
        text=f"Result Set Match: False",
        justify='left',
        font=style_header_text
    )
    res_match_lbl.grid(row=0, column=0, sticky='w')

    recall_score_lbl = tk.Label(
        master=scores_frm,
        text=f"Recall: 1",
        justify='left',
        font=style_header_text
    )
    recall_score_lbl.grid(row=1, column=0, sticky='w')

    precision_score_lbl = tk.Label(
        master=scores_frm,
        text=f"Precision: 1",
        justify='left',
        font=style_header_text
    )
    precision_score_lbl.grid(row=1, column=1, sticky='w')

    f1_score_lbl = tk.Label(
        master=scores_frm,
        text=f"F1: 1",
        justify='left',
        font=style_header_text
    )
    f1_score_lbl.grid(row=1, column=2, sticky='w')

    syntax_error_ct_lbl = tk.Label(
        master=scores_frm,
        text=f"Syntax Errors: 0",
        justify="left",
        font=style_header_text
    )
    syntax_error_ct_lbl.grid(row=2, column=0, sticky='w')

    halucination_ct_lbl = tk.Label(
        master=scores_frm,
        text=f"Hallucinations: 0",
        justify="left",
        font=style_header_text
    )
    halucination_ct_lbl.grid(row=2, column=1, sticky='w')

    scores_frm.grid(row=1, column=1, sticky='w')
    
    # ---- Gold and Predicted Query Frames ----
    q_frms = {}
    for frm_name in ['gold', 'pred']:
        q_frms[frm_name] = tk.Frame(
            master = window,
            relief=tk.RAISED,
            borderwidth=1,
            padx=5,
            pady=2
        )

    
    # ---- Gold query label and text ----
    query_min_width = 80

    gold_label = tk.Label(
        master=q_frms['gold'], 
        text='Gold Query',
        font=style_header_text
        )
    gold_label.pack()
    gold_query = tk.Label(
        master=q_frms['gold'], 
        text='SELECT...',
        justify='left',
        wraplength=500,
        width=query_min_width,
        font=style_query_text
        )
    gold_query.pack()

    # ---- Predicted query label and text ----
    pred_label = tk.Label(
        master=q_frms['pred'], 
        text='Predicted Query',
        font=style_header_text
        )
    pred_label.pack()
    pred_query = tk.Label(
        master=q_frms['pred'], 
        text='SELECT...',
        justify='left',
        wraplength=500,
        width=query_min_width,
        font = style_query_text
        )
    pred_query.pack()

    # ---- Manage gold and predicted form geometries ----
    for i, frm in enumerate(q_frms.keys()):
        q_frms[frm].grid(row=2, column=i, padx=5, pady=3)

    # ---- Schema element matches, mismatches, and Hallucinations
    element_frm = tk.Frame(
        master=window,
        
        )
    matching_lab = tk.Label(
        master = element_frm,
        text = "Schema matches: ",
        justify='left',
        wraplength=500,
        font=style_question_text
    )
    missing_lab = tk.Label(
        master = element_frm,
        text = "Schema missing: ",
        justify='left',
        wraplength=500,
        font=style_question_text
    )
    extra_lab = tk.Label(
        master = element_frm,
        text = "Schema extras: ",
        justify='left',
        wraplength=500,
        font=style_question_text
    )
    matching_lab.grid(row=0, column=0, sticky='w')
    missing_lab.grid(row=1, column=0, sticky='w')
    extra_lab.grid(row=2, column=0, sticky='w')
    element_frm.grid(row=3, column=1, sticky='w')

    # ---- Query navigation buttons ----
    btn_panel_frm = tk.Frame(master=window)
    btn_panel_frm.grid(row=0, column=0, sticky='sw')

    prev_btn = tk.Button(master=btn_panel_frm, text="Prev Question", command=handle_prev_question)
    prev_btn.grid(row=1, column=0)
    next_btn = tk.Button(master=btn_panel_frm, text="Next Question", command=handle_next_question)
    next_btn.grid(row=1, column=1)
    next_ungraded_btn = tk.Button(
        master=btn_panel_frm,
        text="Next Ungraded",
        command=handle_next_ungraded_question
    )
    next_ungraded_btn.grid(row=1, column=2)
    
    # ---- Load Button ----
    modified_var = tk.BooleanVar(value=False)
    load_btn = tk.Button(master=btn_panel_frm, text="Load", command=handle_load_workbook)
    load_btn.grid(row=1, column=3)

    # ---- Save Button ----
    save_btn = tk.Button(master=btn_panel_frm, text="Save", command=handle_save_workbook)
    save_btn.grid(row=1, column=4)

    # ---- Match and next ungraded Button ----
    match_and_next_btn = tk.Button(
        master=btn_panel_frm,
        text="Log Match and Next Ungraded ->",
        command=handle_log_match_and_next_ungraded
    )
    match_and_next_btn.grid(row=1, column=5)

    # ---- Manual match input widgets ----
    match_input_frm = tk.Frame(
        master=window
    )
    man_match_lbl = tk.Label(
        master=match_input_frm,
        text=f"Manual Match: ",
        justify='left',
        font=style_header_text
    )
    man_match_lbl.pack(side=tk.LEFT)
    man_match_var = tk.IntVar()
    man_match_var.set(-1)
    man_match_rad_btn_no = tk.Radiobutton(
        master=match_input_frm,
        text='No',
        variable=man_match_var,
        value=0,
        font=style_header_text,
        command=handle_manual_scoring
        )
    man_match_rad_btn_no.pack(side=tk.LEFT)
    man_match_rad_btn_yes = tk.Radiobutton(
        master=match_input_frm,
        text='Yes',
        variable=man_match_var,
        value=1,
        font=style_header_text,
        command=handle_manual_scoring
        )
    man_match_rad_btn_yes.pack(side=tk.LEFT)
    man_match_rad_btn_un = tk.Radiobutton(
        master=match_input_frm,
        text='Ungraded',
        variable=man_match_var,
        value=-1,
        font=style_header_text,
        command=handle_manual_scoring
        )
    man_match_rad_btn_un.pack(side=tk.LEFT)
    match_input_frm.grid(row=3, column=0)
    
    man_match_txt = tk.Text(
        master=window,
        height=5
        )
    man_match_txt.grid(row=4, column=0)

    # ---- PROGRESS TRACKING ----
    num_ungraded = workbook_var.get().query('manual_match == -1').shape[0]
    num_ungraded_var = tk.IntVar(value=num_ungraded)

    num_ungraded_lab = tk.Label(
        master=window,
        text=f"Remaining Ungraded: {num_ungraded_var.get()}",
        font=style_question_text
    )
    num_ungraded_lab.grid(row=5, column=0, sticky='w')
    

    window.mainloop()


if __name__ == '__main__':
    evaluate_queries_in_workbook()