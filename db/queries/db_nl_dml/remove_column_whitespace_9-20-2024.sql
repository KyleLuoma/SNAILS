
USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblEventDataHerps.[Substrate Temperature]', 'Substrate_Temperature';

alter table tblFieldDataAmphibianCallCounts drop constraint[SSMA_CC$tblFieldDataAmphibianCallCounts$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataAmphibianCallCounts.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataAmphibianCallCounts.[Call Index]', 'Call_Index';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataAmphibianCallCounts.[Number Observed]', 'Number_Observed';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataCoverBoard.[Board #]', 'Board_#';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataCoverBoard.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataGreenCardObservations.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataGreenCardObservations.[Evidence Code]', 'Evidence_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataMinnowTrapSurveys.[Trap #]', 'Trap_#';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataMinnowTrapSurveys.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataSnakeDataCollection.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Notch Code]', 'Notch_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Call Index]', 'Call_Index';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Notch Code]', 'Notch_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Capture Method]', 'Capture_Method';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Substrate Temperature]', 'Substrate_Temperature';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Carapace Length]', 'Carapace_Length';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Carapace Width]', 'Carapace_Width';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Plastron Length]', 'Plastron_Length';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Plastron Width]', 'Plastron_Width';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Trap #]', 'Trap_#';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Trap Type]', 'Trap_Type';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Notch Code]', 'Notch_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluEvidenceCode.[Evidence Code]', 'Evidence_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Species Code]', 'Species_Code';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Scientific Name]', 'Scientific_Name';

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Common Name]', 'Common_Name';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.Invert_Family.[Invert Family]', 'Invert_Family';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.INVERTEBRATES.[Common Name]', 'Common_Name';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.INVERTEBRATES.[Genus species]', 'Genus_species';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.INVERTEBRATES.[OBS TYPE]', 'OBS_TYPE';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.Roadkill.[HWY Mile Marker]', 'HWY_Mile_Marker';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.Roadkill.[number killed]', 'number_killed';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.Roadkill.[Big Game]', 'Big_Game';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.VERTEBRATES.[Common Name]', 'Common_Name';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.VERTEBRATES.[Scientific Name]', 'Scientific_Name';

alter table VERTEBRATES drop constraint[SSMA_CC$VERTEBRATES$OBS TYPE$disallow_zero_length]
;
GO

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.VERTEBRATES.[OBS TYPE]', 'OBS_TYPE';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.WILDLIFE_MASTERLIST.[COMMON NAME]', 'COMMON_NAME';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.WILDLIFE_MASTERLIST.[SCIENTIFIC NAME]', 'SCIENTIFIC_NAME';
