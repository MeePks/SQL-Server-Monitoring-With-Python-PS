param(
    [string]$imageFilePath,
    [string]$htmlFilePath,
    [string]$emailList,
    [string]$otheremail,
    [string]$auditName,
    [string]$serverName,
    [string]$inputData
)

$PSEmailServer='alerts.smtp.ccaintranet.net'


#converting csv to dataframe
$data=ConvertFrom-Csv -InputObject $inputData
$htmldata = $data | Select-Object -Property MountPoint, TotalSpaceTB,UsedSpaceTB,FreeSpaceTB,@{Name='FreePercentage'; Expression={[Math]::Round($_.FreePercentage, 3) }},Remarks |ConvertTo-Html -Fragment
$pattern = '</td><td>(?!OK</td></tr>)[^<]+</td></tr>'
$replacement = '</td><td style="background-color:#FF0000"><10%</td></tr>'
$htmldata= $htmldata -replace $pattern, $replacement


$MailFrom = (Get-culture).textInfo.ToTitleCase($env:UserName+"@Cotiviti.com")
$Message=@"
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <p>Hello Team,</p>
    <p>Please review the SQL Storage of $auditName : $serverName for the date '$((Get-Date).ToString("yyyy-MM-dd"))'.</p>
    $htmlData
    <p>Thank You,<br>Pikesh Maharjan</p>
</body>
</html>
"@

$LocalemailList=$emailList -split ','
$otherEmailList=$otheremail -split ','

$sendMailMessageSplat = @{
    From = $MailFrom
    To = $LocalemailList
    Cc = $otherEmailList
    Subject = $auditName +" ("+$serverName +' ) : SQL Storage Montioring'
    Body = $Message
    BodyAsHtml =$true
    Attachments = $imageFilePath ,$htmlFilePath
    Priority = 'High'
    DeliveryNotificationOption = 'OnSuccess', 'OnFailure'
    SmtpServer = 'alerts.smtp.ccaintranet.net'
}
Send-MailMessage @sendMailMessageSplat