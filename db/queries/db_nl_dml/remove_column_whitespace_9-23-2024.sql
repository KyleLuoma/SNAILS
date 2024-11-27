
USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.Invert_Family.[Invert Family]', 'Invert_Family';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.WILDLIFE_MASTERLIST.[COMMON NAME]', 'COMMON_NAME';

USE CratersWildlifeObservations;
GO
EXEC sp_rename 'dbo.WILDLIFE_MASTERLIST.[SCIENTIFIC NAME]', 'SCIENTIFIC_NAME';
