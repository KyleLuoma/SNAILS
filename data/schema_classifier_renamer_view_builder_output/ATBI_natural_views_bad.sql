CREATE VIEW db_nl.[table_deadwood] AS
SELECT [Data_ID] AS [Data_ID], [Event_ID] AS [Event_ID], [OldPlot] AS [native_identifier_lwr
oldplot    OldPlot
oldplot    oldPlot
Name: N1_identifier, dtype: object], [Module] AS [Module], [Decay] AS [Decay], [MPD] AS [Midpoint_Diameter], [Length] AS [Length], [X_coord] AS [native_identifier_lwr
x_coord    x_coordinate
x_coord    x_coordinate
Name: N1_identifier, dtype: object], [Y_coord] AS [native_identifier_lwr
y_coord    y_coordinate
y_coord    y_coordinate
Name: N1_identifier, dtype: object], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Deadwood];

CREATE VIEW db_nl.[sampling_events] AS
SELECT [Event_ID] AS [Event_ID], [Location_ID] AS [Location_ID], [Event_Date] AS [Event_Date], [Crew_Members] AS [Crew_Members], [Event_Notes] AS [Event_Notes], [Updated_Date] AS [Updated_Date], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Events];

CREATE VIEW db_nl.[table_locations] AS
SELECT [Location_ID] AS [Location_ID], [Plot_ID] AS [Plot_ID], [X_Coord] AS [native_identifier_lwr
x_coord    x_coordinate
x_coord    x_coordinate
Name: N1_identifier, dtype: object], [Y_Coord] AS [native_identifier_lwr
y_coord    y_coordinate
y_coord    y_coordinate
Name: N1_identifier, dtype: object], [Plot_Azimuth] AS [Plot_Azimuth], [Trail] AS [Trail], [Directions] AS [Directions], [SiteDescription] AS [SiteDescription], [Slope] AS [Slope], [Aspect] AS [Aspect], [Slope_shape] AS [Slope_shape], [Topo_Position] AS [topographic_position], [Elevation] AS [Elevation], [A_Horizon] AS [depth_of_a_horizon], [Litter_depth] AS [Litter_depth], [Agriculture] AS [Agriculture], [QuadName] AS [usgs_quad_name], [Logging] AS [Logging], [Fire] AS [Fire], [Pine_beetle] AS [Pine_beetle], [Windstorm] AS [Windstorm], [Hogs] AS [Hogs], [Other_Disturbance] AS [Other_Disturbance], [Loc_Notes] AS [location_notes], [Association_observed] AS [Association_observed], [Eco_Notes] AS [ecological_notes], [PlaceNameID] AS [PlaceNameID], [GIS_Location_ID] AS [gis_feature_id], [Coord_Units] AS [coordinate_distance_units], [Coord_System] AS [coordinate_system], [UTM_Zone] AS [utm_zone], [Datum] AS [Datum], [Est_H_Error] AS [estimated_horizontal_accuracy], [Accuracy_Notes] AS [Accuracy_Notes], [Unit_Code] AS [Unit_Code], [Updated_Date] AS [Updated_Date], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Locations];

CREATE VIEW db_nl.[table_nests] AS
SELECT [Nest_ID] AS [Nest_ID], [Event_ID] AS [Event_ID], [SpCode] AS [native_identifier_lwr
spcode    species_code
spcode    species_code
Name: N1_identifier, dtype: object], [Module] AS [Module], [Presence_First] AS [Presence_First], [Cover] AS [Cover], [Presence_Second] AS [Presence_Second], [R1] AS [presence_class], [R2] AS [cover_class]
FROM dbo.[tbl_Nests];

CREATE VIEW db_nl.[overstory_id] AS
SELECT [Overstory_ID] AS [Overstory_ID], [Event_ID] AS [Event_ID], [TreeTag] AS [TreeTag], [SpCode] AS [native_identifier_lwr
spcode    species_code
spcode    species_code
Name: N1_identifier, dtype: object], [DBH] AS [tree_diameter_at_1.37_meter], [CanPos] AS [canopy_position], [TreeCond] AS [tree_condition], [notes] AS [native_identifier_lwr
notes    notes
notes    Notes
Name: N1_identifier, dtype: object], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Overstory];

CREATE VIEW db_nl.[sapling_data] AS
SELECT [Saplings_ID] AS [Saplings_ID], [Event_ID] AS [Event_ID], [Module] AS [Module], [spcode] AS [native_identifier_lwr
spcode    species_code
spcode    species_code
Name: N1_identifier, dtype: object], [DClass1] AS [woody_stems_1.4m_10cm_dbh_diameter], [DClass2] AS [woody_stems_1.4m_10cm_dbh], [DClass3] AS [woody_stems_1.4m_10cm_dbh_diameter_class], [DClass4] AS [woody_stems_1.4m_10cm_dbh_diameter_class], [Condition] AS [Condition], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Saplings];

CREATE VIEW db_nl.[seedling_data] AS
SELECT [Seedlings_ID] AS [Seedlings_ID], [Event_ID] AS [Event_ID], [oldPlot] AS [native_identifier_lwr
oldplot    OldPlot
oldplot    oldPlot
Name: N1_identifier, dtype: object], [Module] AS [Module], [SpCode] AS [native_identifier_lwr
spcode    species_code
spcode    species_code
Name: N1_identifier, dtype: object], [Density] AS [Density], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Seedlings];

CREATE VIEW db_nl.[tree_tag_location_data] AS
SELECT [Tree_Tag_ID] AS [tree_tag_identifier], [Location_ID] AS [Location_ID], [Tag] AS [Tag], [oldPlot] AS [native_identifier_lwr
oldplot    OldPlot
oldplot    oldPlot
Name: N1_identifier, dtype: object], [Module] AS [Module], [Xcoord] AS [horizontal_location], [Ycoord] AS [vertical_location], [SpCode] AS [native_identifier_lwr
spcode    species_code
spcode    species_code
Name: N1_identifier, dtype: object], [Plot] AS [Plot], [Notes] AS [native_identifier_lwr
notes    notes
notes    Notes
Name: N1_identifier, dtype: object], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_Tree_Tags];

CREATE VIEW db_nl.[witness_tree_id] AS
SELECT [WitnessTree_ID] AS [WitnessTree_ID], [Location_ID] AS [Location_ID], [Witness_SpCode] AS [link_to_tbl_plantspecies_species_code], [Witness_Azimuth] AS [Witness_Azimuth], [Witness_DBH] AS [diameter_breast_height_witness_tree], [Witness_stake] AS [Witness_stake], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tbl_WitnessTrees];

CREATE VIEW db_nl.[tlu_can_position] AS
SELECT [CanPos_Num] AS [tlu_canopyposition_identifier], [CanPos_Name] AS [canopy_position_name], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_Can_Pos];

CREATE VIEW db_nl.[coverclass_number] AS
SELECT [CoverClass_Num] AS [cover_class_number], [CoverClass_Text] AS [CoverClass_Text]
FROM dbo.[tlu_Cover_Cls];

CREATE VIEW db_nl.[decaystage_id] AS
SELECT [DecayStage_ID] AS [DecayStage_ID], [DecayStage_Descr] AS [decay_stage_description], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_DecayStage];

CREATE VIEW db_nl.[tlu_live_dead] AS
SELECT [Cond_Num] AS [condition_number], [Cond_Text] AS [condition_text]
FROM dbo.[tlu_Live_Dead];

CREATE VIEW db_nl.[tlu_module_number] AS
SELECT [Mod_Num] AS [model_number]
FROM dbo.[tlu_Mod_Num];

CREATE VIEW db_nl.[tlu_place_names] AS
SELECT [ID] AS [identifier], [Name] AS [native_identifier_lwr
name    Name
name    name
Name: N1_identifier, dtype: object], [County] AS [County], [State] AS [State], [utmE] AS [utm_easting_coordinate], [utmN] AS [utm_northting_coordinate], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_PlaceNames];

CREATE VIEW db_nl.[plant_species_list] AS
SELECT [genus] AS [genus], [subgenus] AS [subgenus], [species] AS [species], [subspecies] AS [subspecies], [SpeciesCode] AS [SpeciesCode], [Author] AS [Author], [CommonName] AS [CommonName], [SpeciesNotes] AS [SpeciesNotes], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_PlantSpecies];

CREATE VIEW db_nl.[tlu_presence] AS
SELECT [Pres_Num] AS [presence_number], [Pres_Text] AS [presence_description]
FROM dbo.[tlu_Presence];

CREATE VIEW db_nl.[tlu_rest_of_plot] AS
SELECT [Pres_Num] AS [presence_number], [Pres_Text] AS [presence_description]
FROM dbo.[tlu_R1_RestOfPlot];

CREATE VIEW db_nl.[listed_name] AS
SELECT [ListedName] AS [ListedName], [ValidName] AS [ValidName], [Layer] AS [Layer], [Notes] AS [native_identifier_lwr
notes    notes
notes    Notes
Name: N1_identifier, dtype: object], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_Roads_and_Trails];

CREATE VIEW db_nl.[slope_shape] AS
SELECT [Shape] AS [Shape]
FROM dbo.[tlu_Slope_Shape];

CREATE VIEW db_nl.[topographic_position_id] AS
SELECT [ID] AS [identifier], [TopoPosition] AS [topo_position]
FROM dbo.[tlu_topo_position];

CREATE VIEW db_nl.[tree_condition] AS
SELECT [TreeCond_Num] AS [tree_condition_identifier], [TreeCond_Text] AS [tree_condition_description], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tlu_Tree_Cond];

CREATE VIEW db_nl.[true_false_unknown_yes_no] AS
SELECT [Yes_No] AS [Yes_No]
FROM dbo.[tlu_Yes_No];

CREATE VIEW db_nl.[application_table] AS
SELECT [Project] AS [Project], [Park] AS [Park], [User_name] AS [User_name], [Activity] AS [Activity], [UTM_Zone] AS [utm_zone], [Datum] AS [Datum], [Release_ID] AS [Release_ID], [Link_file_path] AS [Link_file_path], [Backup_prompt_startup] AS [Backup_prompt_startup], [Backup_prompt_exit] AS [Backup_prompt_exit], [Compact_be_exit] AS [compact_backend_exit], [Verify_links_startup] AS [Verify_links_startup], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tsys_App_Defaults];

CREATE VIEW db_nl.[application_table_application_release_history] AS
SELECT [Release_ID] AS [Release_ID], [Release_date] AS [Release_date], [Database_title] AS [Database_title], [Version_number] AS [Version_number], [File_name] AS [File_name], [Release_by] AS [Release_by], [Release_notes] AS [Release_notes], [Author_phone] AS [Author_phone], [Author_email] AS [Author_email], [Author_org] AS [organization_nps_unit_code], [Author_org_name] AS [organization_name], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tsys_App_Releases];

CREATE VIEW db_nl.[application_bug_reports] AS
SELECT [Bug_ID] AS [Bug_ID], [Release_ID] AS [Release_ID], [Report_date] AS [Report_date], [Found_by] AS [Found_by], [Reported_by] AS [Reported_by], [Report_details] AS [Report_details], [Fix_date] AS [Fix_date], [Fixed_by] AS [Fixed_by], [Fix_details] AS [Fix_details], [SSMA_TimeStamp] AS [ssma_timestamp]
FROM dbo.[tsys_Bug_Reports];

CREATE VIEW db_nl.[table_times] AS
SELECT [dest] AS [destination], [times] AS [times]
FROM dbo.[tblTimes];

CREATE VIEW db_nl.[sysdiagrams] AS
SELECT [name] AS [native_identifier_lwr
name    Name
name    name
Name: N1_identifier, dtype: object], [principal_id] AS [principal_id], [diagram_id] AS [diagram_id], [version] AS [version], [definition] AS [definition]
FROM dbo.[sysdiagrams];

