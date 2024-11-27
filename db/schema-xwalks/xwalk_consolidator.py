
import os
import pandas as pd


def load_naturalness_lookup_df(filename) -> pd.DataFrame:
    columns = pd.read_excel(filename, sheet_name='distinct-column')
    tables = pd.read_excel(filename, sheet_name='distinct-table')
    columns.rename(columns={'COLUMN_NAME': 'IDENTIFIER'}, inplace=True)
    tables.rename(columns={'TABLE_NAME': 'IDENTIFIER'}, inplace=True)
    combined =  pd.concat([columns, tables])
    combined['IDENTIFIER'] = combined.apply(
        lambda row: row.IDENTIFIER.lower(),
        axis = 1
    )
    combined = combined[['IDENTIFIER', 'FINAL_SCORE']]
    combined = combined.drop_duplicates().dropna(how = 'all')
    combined = combined.set_index('IDENTIFIER')
    return combined

def consolidate_existing_xwalks(
        database: str, 
        filename_suffix: str,
        xwalk_dir = './schema-xwalks/',
        save_to_disk = False,
        naturalness_lookup_file = './schema-scores/consolidated-scores-7-18-2023-2-QAQC.xlsx'
        ) -> pd.DataFrame:

    nat_lookup_df = load_naturalness_lookup_df(naturalness_lookup_file)

    filenames = os.listdir(xwalk_dir + database)
    filenames = [f for f in filenames if f.startswith(database) and filename_suffix in f and 'consolidated' not in f]
    consolidated_xwalk = {
        'source_database': [],
        'table_or_column': [],
        'native_identifier': [],
        'native_naturalness': [],
        'N1_identifier': [],
        'N2_identifier': [],
        'N3_identifier': []
    }
    
    for f in filenames:
        print(f"Adding {f}")
        xwalk = pd.read_csv(xwalk_dir + database + '/' + f)
        table_or_column = 'table'
        if 'columns' in f:
            table_or_column = 'column'
            source_table = f.split('-')[1]
        for row in xwalk.itertuples():
            consolidated_xwalk['source_database'].append(database)
            consolidated_xwalk['table_or_column'].append(table_or_column)

            if table_or_column == 'column':
                consolidated_xwalk['native_identifier'].append(row.COLUMN_NAME)
                try:
                    consolidated_xwalk['native_naturalness'].append(nat_lookup_df.loc[row.COLUMN_NAME.lower()]['FINAL_SCORE'])
                except:
                    consolidated_xwalk['native_naturalness'].append("UNK")

            else:
                consolidated_xwalk['native_identifier'].append(row.TABLE_NAME)
                try:
                    consolidated_xwalk['native_naturalness'].append(nat_lookup_df.loc[row.TABLE_NAME.lower()]['FINAL_SCORE'])
                except:
                    consolidated_xwalk['native_naturalness'].append("UNK")

            consolidated_xwalk['N1_identifier'].append(row.N1)
            consolidated_xwalk['N2_identifier'].append(row.N2)
            consolidated_xwalk['N3_identifier'].append(row.N3)

    consolidated_df = pd.DataFrame(consolidated_xwalk)
    consolidated_df = consolidated_df.drop_duplicates().dropna(how = 'all')

    if save_to_disk:
        consolidated_df.to_csv(
            f'{xwalk_dir}{database}/{database}-consolidated-xwalk-{filename_suffix}.csv',
            index=False
            )



if __name__ == '__main__':
    consolidate_existing_xwalks(
        'NTSB', 
        'GPT-FT-Corrected',
        save_to_disk=True
        )