Use Amazon
GO

Create View dbo._vw_CheckTierSpace
AS
SELECT 
		 [MountPoint], 
		 PARSENAME(CONVERT(VARCHAR,CAST([TotalSpaceGB] AS MONEY),1),2) AS [TotalSpaceGB], 
		 PARSENAME(CONVERT(VARCHAR,CAST([UsedSpaceGB] AS MONEY),1),2) AS [UsedSpaceGB], 
		 --CAST(100 - CAST(PercentFree AS tinyint) AS VARCHAR(5)) + ''%'' AS [PercentUsed], 
		 PARSENAME(CONVERT(VARCHAR,CAST([FreeSpaceGB] AS MONEY),1),2) AS [FreeSpaceGB], 
		 --cast(PercentFree as varchar(20)) + ''%'' AS [PercentFree],
		 cast(convert(decimal(6,2),PercentFree) as varchar(20)) + '%' AS PercentFree,
		 CASE WHEN PercentFree < 5 THEN '< 5%' ELSE 'OK' END As Remarks
	--INTO #Temp_TierSpace
	FROM 
	(
		SELECT 
			DISTINCT 
					replace(vs.volume_mount_point, 'D:\SQLData_AFS\', '') AS [MountPoint], 
					(((vs.total_bytes - vs.available_bytes)/1024.00/1024/1024)/(vs.total_bytes/1024/1024/1024)* 100) as PercentUsed, 
					(((vs.available_bytes)/1024.00/1024/1024)/(vs.total_bytes/1024/1024/1024)* 100) as PercentFree, 
					(vs.total_bytes/1024/1024/1024) AS [TotalSpaceGB], 
					((vs.total_bytes - vs.available_bytes)/1024/1024/1024) AS [UsedSpaceGB], 
					(vs.available_bytes/1024/1024/1024) AS [FreeSpaceGB] --select *
		FROM 
			sys.master_files AS f CROSS APPLY sys.dm_os_volume_stats(f.database_id, f.file_id) AS vs
	) tbl
	where tbl.[MountPoint]  LIKE '%Amazon%' 
	

DECLARE @To                     AS VARCHAR(MAX) = [Cnly].[Utility].[UserNameClean](SUSER_SNAME()) + '@gmail.com'
DECLARE @Subject                AS VARCHAR(MAX)
DECLARE @Result                 AS TINYINT
DECLARE @MailOutput             AS XML
DECLARE @Txt                    AS VARCHAR(MAX) = ''
DECLARE @RecTxt                 AS VARCHAR(MAX) = ''
DECLARE @Ctr                    AS SMALLINT = 1
DECLARE @RowCt                  AS SMALLINT
DECLARE @AttnFlag               AS TINYINT = 0
DECLARE @LogText                AS VARCHAR(MAX)
DECLARE @CurServerName Varchar(30)=@@SERVERNAME
DECLARE @Cc VARCHAR(8000)='Pikesh.Maharjan@gmail.com;'
SET @Subject = @Subject + ': Attention Needed'

SET @Txt = @Txt + '<table border="1">'
	SET @Txt = @Txt + '<tr>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="200">MountPoint</th>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="100">Total Space(GB)</th>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="100">Used Space(GB)</th>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="100">Free Space(GB)</th>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="100">Free Space Percentage</th>'
	SET @Txt = @Txt + '<th style="background-color:#cce6ff" width="100">Remarks</th>'
	SET @Txt = @Txt + '</tr>'

	Set @TXT= @TXT +'<img src="D:\Storage Monitoring\Capture.PNG" alt="Image Description">'

EXEC Cnly.Mail.SqlNotifySend @Subject, @To,@Cc, NULL, @Txt, @Result OUT, @MailOutput OUT, 0, 1

