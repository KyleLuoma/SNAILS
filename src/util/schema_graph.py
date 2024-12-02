# SchemaGraph v1.0


import src.util.db_util as db_util
import pandas as pd
import igraph as ig
from collections import defaultdict

class SchemaGraph():

    manual_pkfk = {
    "PacificIslandLandbirds": [
        ("tbl_events", "station_id", 1, "manual_fk_events_station", "tbl_stations$primarykey", "tbl_stations", "station_id", 1),
        ("tbl_detections", "observation_id", 1, "manual_fk_detections_observations", "tbl_observations$primarykey", "tbl_observations", "observation_id", 1)
    ]
    }

    def __init__(
            self, 
            database_name: str, 
            repair_constraints: bool = True,
            use_single_starting_table_for_connections: bool = False
            ):
        self.database = database_name
        self.repair_constraints = repair_constraints
        if self.database not in SchemaGraph.manual_pkfk:
            self.repair_constraints = False
        self.single_starting_table = use_single_starting_table_for_connections

        self.edge_type_weights = {
            "table-column": 1.0,
            "pk-column": 1.0,
            "fk-pk": 1.0,
            "column-fk": 1.0
        }

        self.vertex_colors = {
            "table": "blue",
            "pk": "red",
            "fk": "green",
            "column": "purple"
        }

        self.pkfk_df = self._construct_pkfk_dataframe()
        self.orphan_tables = self._construct_orphan_table_list()
        vertice_lookup_dicts = self._construct_vertice_lookup_dicts()
        self.vertice_type_lookup = vertice_lookup_dicts["vertice_type_lookup"]
        self.vertice_name_lookup = vertice_lookup_dicts["vertice_name_lookup"]
        self.name_vertice_lookup = vertice_lookup_dicts["name_vertice_lookup"]
        self.all_vertices = vertice_lookup_dicts["all_vertices"]
        edge_data = self._construct_edges()
        self.edges = edge_data["edges"]
        self.edge_type_lookup = edge_data["edge_type_lookup"]
        self.edge_weight_lookup = edge_data["edge_weight_lookup"]
        self.schema_graph = self._construct_graph()



    def _construct_graph(self):
        g = ig.Graph(
            n=len(self.all_vertices),
            edges=self.edges
        )
        return g



    def _construct_pkfk_dataframe(self) -> pd.DataFrame:
        with open("./db/queries/db_nl_dml/get_fk_pk_from_mssql.sql") as f:
            query = f.read()
        pkfk_df = db_util.do_query(
            query,
            self.database,
            debug=False
            )
        if pkfk_df.shape[0] == 0:
            return pkfk_df
        for column in pkfk_df.columns:
            if "ordinal" not in column:
                pkfk_df[column] = pkfk_df[column].str.lower()
        if self.repair_constraints:
            pkfk_df = self._repair_constraints(pkfk_df)
        return pkfk_df
    


    def _construct_orphan_table_list(self, pkfk_df: pd.DataFrame = None) -> list:
        if pkfk_df == None:
            pkfk_df = self.pkfk_df
        with open("./db/queries/db_nl_dml/get_orphan_tables.sql") as f:
            orphan_query = f.read()
        orphans = db_util.do_query(
            orphan_query,
            self.database
        )
        if orphans.shape[0] == 0:
            return []
        orphans = orphans["table_name"].str.lower().to_list()
        referenced_pks = pkfk_df.pk_table.to_list()
        orphans = set(orphans).difference(set(referenced_pks))
            
        if self.repair_constraints:
            repaired_tables = [row[0] for row in SchemaGraph.manual_pkfk[self.database]]
        else:
            repaired_tables = []
        orphans = [t for t in orphans if t not in repaired_tables]
        return orphans



    def _construct_vertice_lookup_dicts(
            self, 
            pkfk_df: pd.DataFrame = None,
            orphans: list = None
            ) -> dict:
        if pkfk_df == None:
            pkfk_df = self.pkfk_df
        if orphans == None:
            orphans = self.orphan_tables
        vertice_type_lookup = {}
        tables = pkfk_df.pk_table.unique().tolist() + pkfk_df.fk_table.unique().tolist()
        tables = set(tables + orphans)
        for table in tables:
            vertice_type_lookup[table] = "table"

        table_columns = [
            row.pk_table + "." + row.pk_column 
            for row in pkfk_df.itertuples()
            ]
        table_columns += [
            row.fk_table + "." + row.fk_column 
            for row in pkfk_df.itertuples()
            ]
        table_columns = set(table_columns)
        for column in table_columns:
            vertice_type_lookup[column] = "column"

        pk_constraints = set(pkfk_df.pk_constraint_name)
        fk_constraints = set(pkfk_df.fk_constraint_name)
        for c in pk_constraints:
            vertice_type_lookup[c] = "pk"
        for c in fk_constraints:
            vertice_type_lookup[c] = "fk"
        all_vertices = list(tables) + list(table_columns) + list(pk_constraints) + list(fk_constraints)
        vertice_name_lookup = {x : all_vertices[x] for x in range(0, len(all_vertices))}
        name_vertice_lookup = {vertice_name_lookup[k]: k for k in vertice_name_lookup}
        return{
            "vertice_type_lookup": vertice_type_lookup,
            "vertice_name_lookup": vertice_name_lookup,
            "name_vertice_lookup": name_vertice_lookup,
            "all_vertices": all_vertices
        }



    def _construct_edges(
            self, 
            pkfk_df: pd.DataFrame = None,
            all_vertices: list = None,
            name_vertice_lookup: dict = None,
            vertice_name_lookup: dict = None
            ) -> dict:
        if pkfk_df  == None:
            pkfk_df = self.pkfk_df
        if all_vertices == None:
            all_vertices = self.all_vertices
        if name_vertice_lookup == None:
            name_vertice_lookup = self.name_vertice_lookup
        if vertice_name_lookup == None:
            vertice_name_lookup = self.vertice_name_lookup

        t_col_edge_dict = defaultdict(list)
        edge_type_lookup = {}
        edge_weight_lookup = {}
        for v in all_vertices:
            if "." in v:
                t_col_edge_dict[v.split(".")[0]].append(v)
        t_col_edges = []
        for t in t_col_edge_dict:
            for c in t_col_edge_dict[t]:
                t_col_edge = [name_vertice_lookup[t], name_vertice_lookup[c]]
                t_col_edge = sorted(t_col_edge)
                t_col_edges.append(t_col_edge)
                edge_type_lookup[tuple(t_col_edge)] = "table-column"
                edge_weight_lookup[tuple(t_col_edge)] = self.edge_type_weights["table-column"]

        pkfk_edges = []
        for row in pkfk_df.itertuples():
            col_fk_edge = [
                name_vertice_lookup[row.fk_table + "." + row.fk_column],
                name_vertice_lookup[row.fk_constraint_name]
                ]
            col_fk_edge = sorted(col_fk_edge)
            if col_fk_edge not in pkfk_edges:
                pkfk_edges.append(col_fk_edge)
                edge_type_lookup[tuple(col_fk_edge)] = "column-fk"
                edge_weight_lookup[tuple(col_fk_edge)] = self.edge_type_weights["column-fk"]

            fk_pk_edge = [
                    name_vertice_lookup[row.fk_constraint_name], 
                    name_vertice_lookup[row.pk_constraint_name]
                    ]
            fk_pk_edge = sorted(fk_pk_edge)
            if fk_pk_edge not in pkfk_edges:
                pkfk_edges.append(fk_pk_edge)
                edge_type_lookup[tuple(fk_pk_edge)] = "fk-pk"
                edge_weight_lookup[tuple(fk_pk_edge)] = self.edge_type_weights["fk-pk"]

            pk_col_edge = [
                name_vertice_lookup[row.pk_constraint_name], 
                name_vertice_lookup[row.pk_table + "." + row.pk_column]
                ]
            pk_col_edge = sorted(pk_col_edge)
            if pk_col_edge not in pkfk_edges:
                pkfk_edges.append(pk_col_edge)    
                edge_type_lookup[tuple(pk_col_edge)] = "pk-column"
                edge_weight_lookup[tuple(pk_col_edge)] = self.edge_type_weights["pk-column"]

        return {
            "edges": t_col_edges + pkfk_edges,
            "edge_type_lookup": edge_type_lookup,
            "edge_weight_lookup": edge_weight_lookup
        }
    


    def _repair_constraints(self, pkfk_df: pd.DataFrame):
        manual_pkfk_df = pd.DataFrame({
            column: [
                row[ix] for row in SchemaGraph.manual_pkfk[self.database]
                ] for ix, column in enumerate(pkfk_df.columns)
        })

        pkfk_df = pd.concat([
            pkfk_df,
            manual_pkfk_df
        ])
        return pkfk_df
    


    def get_schema_identifiers_between_tables(
            self,
            table_names: list
    ) -> dict:
        table_names = [t.lower() for t in table_names]
        connector_tables_columns = defaultdict(list)
        connections = self.get_table_connections(table_names=table_names)
        for v in connections["vertex_labels"]:
            if self.vertice_type_lookup[v] == "column":
                connector_tables_columns[v.split(".")[0]].append(
                    v.split(".")[1]
                    )
        return connector_tables_columns



    def get_table_connections(self, table_names: list) -> dict:
        table_vertices = [
            self.name_vertice_lookup[t] for t in table_names
        ]
        connectors = self.get_connecting_vertices_and_edges(table_vertices)
        connecting_vertices = connectors["vertices"]
        return {
            "vertex_ids": connecting_vertices,
            "vertex_labels": [self.vertice_name_lookup[v] for v in connecting_vertices],
            "edges": connectors["edges"]
        }



    def get_connecting_vertices_and_edges(
            self, 
            vertices: list,
            single_starting_table: bool = None
            ) -> dict:
        if single_starting_table == None:
            single_starting_table = self.single_starting_table
        if len(vertices) <= 1:
            return {
                    "vertices": list(vertices),
                    "edges": []           
                    }
        path_vertices = set()
        path_edges = set()
        path_combos = set()
        for t1 in vertices:
            for t2 in vertices:
                if t1 == t2:
                    continue
                path_combos.add(tuple(sorted([t1, t2])))

        if single_starting_table:
            
            vertices = list(set(vertices))
            starting_table = vertices[0]
            to_tables = vertices[1:]
            path_candidates = []

            starting_table_ix = 0
            while(len(path_candidates) == 0 and starting_table_ix < len(vertices) - 1):
                path_candidates = self.schema_graph.get_all_simple_paths(
                    v=starting_table,
                    to=to_tables
                )
                starting_table_ix += 1
                starting_table = vertices[starting_table_ix]
                to_tables = vertices[0:starting_table_ix] + vertices[starting_table_ix + 1:]
            if len(path_candidates) == 0:
                return {
                    "vertices": list(),
                    "edges": list()           
                }

            journeys = set()
            for t in to_tables:
                journeys.add((starting_table, t))

            journey_minpaths = {}
            for journey in journeys:
                min_path_val = 10000
                min_path_ix = 0
                for i, path in enumerate(path_candidates):
                    if len(path) < min_path_val and path[0] == journey[0] and path[-1] == journey[-1]:
                        min_path_val = len(path)
                        min_path_ix = i
                min_join_path = path_candidates[min_path_ix]
                if len(min_join_path) > 1:
                    path_edges = [
                        [min_join_path[i], min_join_path[i + 1]] for i in range(0, len(min_join_path) - 1)
                        ]
                    journey_minpaths[journey] = path_edges

            path_edges = set()
            for jmp in journey_minpaths:
                for edg in journey_minpaths[jmp]:
                    path_edges.add(tuple(sorted(edg)))

            for edge in path_edges:
                path_vertices = path_vertices.union(edge)

            return {
                "vertices": list(path_vertices),
                "edges": path_edges           
            }

        for path_combo in path_combos:
            path_candidates = self.schema_graph.get_all_simple_paths(
                v=path_combo[0],
                to=path_combo[1]
            )
            if len(path_candidates) == 0:
                continue
            min_path_val = 10000
            min_path_ix  = 0
            for ix, path in enumerate(path_candidates):
                if len(path) < min_path_val:
                    min_path_ix = ix
                    min_path_val = len(path)
            min_path = path_candidates[min_path_ix]
            path_vertices = path_vertices.union(
                set(min_path)
                )
            path_edges = [
                tuple(sorted([min_path[i], min_path[i + 1]]))
                for i in range(0, len(min_path) - 1)
            ]
            path_edges = list(set(path_edges))
        return {
            "vertices": list(path_vertices),
            "edges": path_edges           
            }

                

    

if __name__ == "__main__":
    db_util.do_query(
        "select * from AAAR",
        "SBODemoUS"
    )
    sg = SchemaGraph(
        "SBODemoUS",
        use_single_starting_table_for_connections=True
        )
    table_connections = sg.get_schema_identifiers_between_tables([
        "tbl_Locations", "tlu_Cover_Cls"
    ])
    print(table_connections)
    print("\nOrphans:", sg.orphan_tables)
    