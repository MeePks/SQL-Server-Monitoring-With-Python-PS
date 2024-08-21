#importing necessdary libraries
import pyodbc
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as offline
from datetime import datetime
import os
import subprocess
import configparser as cfg

#Functions to open and close connections
def open_connection(server_name,database_name):
    try:
        conn_string=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={database_name};Trusted_connection=yes;'
        conn=pyodbc.connect(conn_string)
        cursor=conn.cursor()
        print(f"Sucessfully Connected to the server: {server_name}")
        return conn,cursor
    except pyodbc.Error as e:
        print(f"Error connecting to the server: {e}")

def close_connection(conn):
    try:
        dsn=conn.getinfo(pyodbc.SQL_SERVER_NAME)
        conn.close()
        print(f"Terminated the Connection:{dsn}")
    except:
        print(f"Error closing the Requested server:{dsn}")

#Funtion to visulaize the dataframe returned by the query
def visualize_disk_space(df_data,server_name,audit_name,audit_detail):
    #converting the data types to numeric values:
    df_data['UsedSpaceTB']=pd.to_numeric(df_data['UsedSpaceTB'],errors='coerce')
    df_data['FreeSpaceTB']=pd.to_numeric(df_data['FreeSpaceTB'],errors='coerce')
    df_data['TotalSpaceTB']=pd.to_numeric(df_data['TotalSpaceTB'],errors='coerce')

    #calculating the percentages:
    df_data['UsedPercentage'] = (df_data['UsedSpaceTB'] / df_data['TotalSpaceTB']) * 100
    df_data['FreePercentage'] = (df_data['FreeSpaceTB'] / df_data['TotalSpaceTB']) * 100

    #determining the colours based on Remarks column 
    df_data['UsedSpaceColor']=df_data['Remarks'].apply(lambda x: 'rgba(255,0,0,0.6)' if x!='OK' else 'rgb(55,83,109)')
    df_data['FreeSpaceColor']=df_data['Remarks'].apply(lambda x: 'rgba(255,165,0,0.6)' if x!='OK' else 'rgb(26,118,255)')

    #creating text annotations for ued and free space
    df_data['UsedSpaceText'] = df_data.apply(lambda row: f"{row['UsedSpaceTB']}TB ({row['UsedPercentage']:.2f}%)", axis=1)
    df_data['FreeSpaceText'] = df_data.apply(lambda row: f"{row['FreeSpaceTB']}TB ({row['FreePercentage']:.2f}%)", axis=1)

    #creating the figure now
    fig=go.Figure()

    #add used space bar
    fig.add_trace(go.Bar(
        x=df_data['MountPoint'],
        y=df_data['UsedSpaceTB'],
        name='Used Space',
        marker=dict(color=df_data['UsedSpaceColor']),
        text=df_data['UsedSpaceText'],
        textposition='inside'
    ))

    fig.add_trace(go.Bar(
        x=df_data['MountPoint'],
        y=df_data['FreeSpaceTB'],
        name='Free Space',
        marker=dict(color=df_data['FreeSpaceColor']),
        text=df_data['FreeSpaceText'],
        textposition='inside'
    ))

    # Update layout
    fig.update_layout(
    title='SQL Storage Usage by Mount Point',
    xaxis=dict(title='Mount Points'),
    yaxis=dict(title='Space (TB)'),
    barmode='stack',
    legend=dict(orientation='h', yanchor='bottom',y=1.02, xanchor='right',x=1)
    )

    #converting the figure into image and html format
    html_content=offline.plot(fig,output_type='div',include_plotlyjs='cdn')
    image_bytes=fig.to_image(format='png',width=1024,height=800)
    img_path=f'{reportPath}\\{audit_name}\{today_date}\plot_{server_name}.png'
    html_path=f'{reportPath}\\{audit_name}\{today_date}\plot_{server_name}.html'

    if not os.path.exists(f'{reportPath}\\{audit_name}\{today_date}'):
        os.makedirs(f'{reportPath}\\{audit_name}\{today_date}')

    with open(f'{reportPath}\\{audit_name}\{today_date}\plot_{server_name}.png','wb') as f:
        f.write(image_bytes)

    with open(f'{reportPath}\\{audit_name}\{today_date}\plot_{server_name}.html','w') as f:
        f.write(html_content)


    #converting dataframe into csv
    csv_data=df_data.to_csv(index=False)
    csv_data_str=csv_data
    

    send_email(audit_detail,img_path,html_path,audit_name,server_name,csv_data_str)



def send_email(audit_detail,img_path,html_path,audit_name,server_name,csv_data_str):
    localEmailList=audit_detail.PrimaryContact 
    cc=audit_detail.SecondaryContact
    subprocess.run(['powershell.exe','-File', 'SendEmail.ps1',
                img_path,
                html_path,
                localEmailList,
                cc,
                audit_name,
                server_name,
                csv_data_str])


#databse connection string to pull the neccesary details
config=cfg.ConfigParser()
config.read('config.ini')

srv=config['main']['srvname']
db=config['main']['dbname']
reportPath=config['main']['reportpath']
tblname=config['main']['tblname']
print(reportPath)

conn,cursor=open_connection(srv,db)
    
#query to pull out the auditDetails
query=f'''select [Id]
      ,AuditName
      ,ServerName
      ,PrimaryContact
      ,Isnull(SecondaryContact,'') SecondaryContact
      from {tblname}
      '''
cursor.execute(query)
audit_details=cursor.fetchall()
close_connection(conn)

#declaring necessary variables
reportPath='\\\ccaintranet.com\dfs-dc-01\Data\Retail\WalmartMX\Development\Pikesh.Maharjan\Storage Monitoring\Reports'
today_date=datetime.today().strftime('%Y-%m-%d')
query_disc_details='''
SELECT Distinct
		 [MountPoint], 
		 CAST([TotalSpaceTB] AS decimal(16,2)) AS [TotalSpaceTB], 
		 CAST([UsedSpaceTB] AS decimal(16,2)) AS [UsedSpaceTB], 
		 CAST([FreeSpaceTB] AS decimal(16,2)) AS [FreeSpaceTB], 
		 cast(convert(decimal(6,2),PercentFree) as varchar(20)) + '%' AS PercentFree,
		 CASE WHEN PercentFree < 10 THEN '< 10%' ELSE 'OK' END As Remarks
	FROM 
	(
SELECT 
			DISTINCT 
					replace(vs.volume_mount_point, 'D:\SQLData_AFS\', '') AS [MountPoint], 
					(((vs.total_bytes - vs.available_bytes)/1024.00/1024/1024)/(vs.total_bytes/1024/1024/1024)* 100) as PercentUsed, 
					(((vs.available_bytes)/1024.00/1024/1024)/(vs.total_bytes/1024/1024/1024)* 100) as PercentFree, 
					(vs.total_bytes/1024.000/1024/1024/1024) AS [TotalSpaceTB], 
					((vs.total_bytes - vs.available_bytes)/1024.000/1024/1024/1024) AS [UsedSpaceTB], 
					(vs.available_bytes/1024.000/1024/1024/1024) AS [FreeSpaceTB]
		FROM 
			sys.master_files AS f CROSS APPLY sys.dm_os_volume_stats(f.database_id, f.file_id) AS vs
			) tbl
	where tbl.[MountPoint]  LIKE ?
    order by MountPoint
'''

#Iterating over Audit Details To pull out necessary Informations.
df_data_logs=pd.DataFrame()
for audit_detail in audit_details:
    audit_name=audit_detail.AuditName
    server_name=audit_detail.ServerName
    audit_name_param=f"%{audit_name}%"
    print(audit_name)
    conn,cursor=open_connection(server_name,audit_name)
    df_data=pd.read_sql_query(query_disc_details,conn,params=[audit_name_param])
    df_data_logs=pd.concat([df_data_logs,df_data])
    close_connection(conn)

df_data_logs.to_csv('Storage.csv')



            

