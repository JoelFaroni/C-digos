import boto3
from botocore.exceptions import NoCredentialsError

def create_s3_bucket(bucket_name, region=None):
    s3 = boto3.client('s3', region_name=region)
    
    if region:
        location = {'LocationConstraint': region}
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
    else:
        s3.create_bucket(Bucket=bucket_name)
    
    print(f"Bucket {bucket_name} criado com sucesso.")

def create_backup_plan():
    backup_client = boto3.client('backup')
    
    backup_plan = {
        'BackupPlanName': 'MeuPlanoDeBackupDiario',
        'Rules': [
            {
                'RuleName': 'RegraDiaria',
                'TargetBackupVaultName': 'MeuCofreDeBackups',
                'ScheduleExpression': 'cron(0 18 * * ? *)', # Diariamente às 18:00 (6 PM)
                'StartWindowMinutes': 60,
                'CompletionWindowMinutes': 10080, # 7 dias
                'Lifecycle': {
                    'MoveToColdStorageAfterDays': 30,
                    'DeleteAfterDays': 365
                },
                'RecoveryPointTags': {
                    'Projeto': 'BackupDiario'
                }
            }
        ]
    }
    
    response = backup_client.create_backup_plan(
        BackupPlan=backup_plan
    )
    
    print(f"Backup Plan ID: {response['BackupPlanId']}")

def upload_to_s3(local_file, bucket, s3_file):
    s3 = boto3.client('s3')
    
    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload bem-sucedido")
    except FileNotFoundError:
        print("Arquivo não encontrado")
    except NoCredentialsError:
        print("Credenciais não disponíveis")

def upload_to_glacier(vault_name, file_path):
    glacier = boto3.client('glacier')
    
    with open(file_path, 'rb') as file:
        response = glacier.upload_archive(
            vaultName=vault_name,
            body=file
        )
    print(f"Archive ID: {response['archiveId']}")

def create_cloudwatch_alarm():
    cloudwatch = boto3.client('cloudwatch')
    
    alarm = cloudwatch.put_metric_alarm(
        AlarmName='BackupFalhou',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='FailedBackupJobs',
        Namespace='AWS/Backup',
        Period=300,
        Statistic='Sum',
        Threshold=1.0,
        ActionsEnabled=False,
        AlarmActions=[
            'arn:aws:sns:REGION:ACCOUNT_ID:MyTopic'
        ],
        AlarmDescription='Alerta para jobs de backup falhados',
        Dimensions=[
            {
                'Name': 'BackupVaultName',
                'Value': 'MeuCofreDeBackups'
            }
        ]
    )
    
    print("Alarme criado com sucesso.")

def download_from_s3(bucket, s3_file, local_file):
    s3 = boto3.client('s3')
    
    try:
        s3.download_file(bucket, s3_file, local_file)
        print("Download bem-sucedido")
    except FileNotFoundError:
        print("Arquivo não encontrado")
    except NoCredentialsError:
        print("Credenciais não disponíveis")

create_s3_bucket('meu-novo-bucket', 'us-east-1')
create_backup_plan()
upload_to_s3('meuarquivo.txt', 'meu-novo-bucket', 'backup/meuarquivo.txt')
upload_to_glacier('meu-cofre', 'meuarquivo.txt')
create_cloudwatch_alarm()
download_from_s3('meu-novo-bucket', 'backup/meuarquivo.txt', 'meuarquivo_restaurado.txt')
