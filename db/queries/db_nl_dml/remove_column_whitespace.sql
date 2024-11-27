
USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataAmphibianCallCounts.[Species Code]', 'Species_Code';

alter table tblFieldDataAmphibianCallCounts drop constraint[SSMA_CC$tblFieldDataAmphibianCallCounts$Call Index$validation_rule]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataAmphibianCallCounts.[Call Index]', 'Call_Index';

alter table tblFieldDataCoverBoard drop constraint[SSMA_CC$tblFieldDataCoverBoard$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataCoverBoard.[Species Code]', 'Species_Code';

alter table tblFieldDataGreenCardObservations drop constraint[SSMA_CC$tblFieldDataGreenCardObservations$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataGreenCardObservations.[Species Code]', 'Species_Code';

alter table tblFieldDataGreenCardObservations drop constraint[SSMA_CC$tblFieldDataGreenCardObservations$Evidence Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataGreenCardObservations.[Evidence Code]', 'Evidence_Code';

alter table tblFieldDataMinnowTrapSurveys drop constraint[SSMA_CC$tblFieldDataMinnowTrapSurveys$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataMinnowTrapSurveys.[Species Code]', 'Species_Code';

alter table tblFieldDataSnakeDataCollection drop constraint[SSMA_CC$tblFieldDataSnakeDataCollection$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataSnakeDataCollection.[Species Code]', 'Species_Code';

alter table tblFieldDataTimeConstrainedSearches drop constraint[SSMA_CC$tblFieldDataTimeConstrainedSearches$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Species Code]', 'Species_Code';

alter table tblFieldDataTimeConstrainedSearches drop constraint[SSMA_CC$tblFieldDataTimeConstrainedSearches$Notch Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Notch Code]', 'Notch_Code';

alter table tblFieldDataTimeConstrainedSearches drop constraint[SSMA_CC$tblFieldDataTimeConstrainedSearches$Call Index$validation_rule]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTimeConstrainedSearches.[Call Index]', 'Call_Index';

alter table tblFieldDataTurtleMeasurements drop constraint[SSMA_CC$tblFieldDataTurtleMeasurements$Notch Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Notch Code]', 'Notch_Code';

alter table tblFieldDataTurtleMeasurements drop constraint[SSMA_CC$tblFieldDataTurtleMeasurements$Capture Method$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Capture Method]', 'Capture_Method';

alter table tblFieldDataTurtleMeasurements drop constraint[SSMA_CC$tblFieldDataTurtleMeasurements$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleMeasurements.[Species Code]', 'Species_Code';

alter table tblFieldDataTurtleTrapSurveys drop constraint[SSMA_CC$tblFieldDataTurtleTrapSurveys$Trap Type$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Trap Type]', 'Trap_Type';

alter table tblFieldDataTurtleTrapSurveys drop constraint[SSMA_CC$tblFieldDataTurtleTrapSurveys$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Species Code]', 'Species_Code';

alter table tblFieldDataTurtleTrapSurveys drop constraint[SSMA_CC$tblFieldDataTurtleTrapSurveys$Notch Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tblFieldDataTurtleTrapSurveys.[Notch Code]', 'Notch_Code';

alter table tluEvidenceCode drop constraint[SSMA_CC$tluEvidenceCode$Evidence Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluEvidenceCode.[Evidence Code]', 'Evidence_Code';

alter table tluSpecies drop constraint[SSMA_CC$tluSpecies$Species Code$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Species Code]', 'Species_Code';

alter table tluSpecies drop constraint[SSMA_CC$tluSpecies$Scientific Name$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Scientific Name]', 'Scientific_Name';

alter table tluSpecies drop constraint[SSMA_CC$tluSpecies$Common Name$disallow_zero_length]
;
GO

USE ASIS_20161108_HerpInv_Database;
GO
EXEC sp_rename 'dbo.tluSpecies.[Common Name]', 'Common_Name';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.VERTEBRATES.[OBS TYPE]', 'OBS_TYPE';
