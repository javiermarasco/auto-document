import os
import json

base_template = '''
<body>
    <table style="border: 1px solid black;">
        <th style="border: 1px solid black;">Name</th>
        <th style="border: 1px solid black;">Connection string</th>
        <th style="border: 1px solid black;">IPs</th>
        {tr}
    </table>
</body>
'''

temporal_tr = ''
for root, subdirectories, files in os.walk(os.path.dirname(__file__)+'/configs'):    
    for file in files: 
        print("Processing file -> %s" % (os.path.join(root, file)))
        if file.__contains__('.json'):
            temporal_tr += '<tr>'
            config_file = os.path.join(os.path.dirname(__file__), os.path.join(root, file))
            with open(config_file, 'r') as read_json:
                content_json = json.load(read_json)
                temporal_tr += '<td style="border: 1px solid black;">'
                temporal_tr += content_json['Name']
                temporal_tr += '</td>'
                temporal_tr += '<td style="border: 1px solid black;">'
                temporal_tr += content_json['ConnectionString']
                temporal_tr += '</td>'
                temporal_tr += '<td style="border: 1px solid black;">'
                temporal_tr += ' '.join(content_json['IPs'])
                temporal_tr += '</td>'
            temporal_tr += '</tr>'

path_html = os.path.join(os.path.dirname(__file__), 'index.html')
with open(path_html, 'w') as write_base:
    write_base.write(base_template)
tmpl = open(path_html, 'rt').read()
text = tmpl.format(tr=temporal_tr)
with open(path_html, 'w') as writer:
    writer.write(text)


page_id = '' # You must create the page in confluence first to provide a page id.
user = '' # this is the email you used to open your free confluence account.
token = '' # This is a token for your account, known as personal access token as well.
url = 'https://<your-name>.atlassian.net/wiki/rest/api/content/%s' % (page_id)
account_conn_str = '' # This is the connection string for your Azure storage account.



def publish_to_confluence(user,token,url,page_id,title,content):
    import requests
    confluence_page_version_url = '%s?expand=version' % (url)
    page_current_version = requests.get(url=confluence_page_version_url, auth=(user,token)).json()['version']['number']
    content = content.replace('\n','')
    content = content.replace('"', "'")
    body = '''
    {"id":"%s","type":"page", "title":"%s","body":{"storage":{"value": "%s","representation":"storage"}}, "version":{"number":%i}}
    ''' % (page_id, title, content,page_current_version + 1)
    update_page_content = requests.put(url=url, auth=(user,token), data=body.replace('\n',''), headers={'content-type': 'application/json'})

def clean_old_versions(user,token,url,threshold):
    import requests
    versions = requests.get(url='%s/version' % (url), headers={'content-type': 'application/json'},auth=(user,token))

    if len(versions.json()['results']) >= threshold:
        max = len(versions.json()['results'])
        amount_to_delete = max - threshold
        while amount_to_delete >= 0:
            deleted = requests.delete(url='%s/version/%s' % (url,max-amount_to_delete),auth=(user,token),headers={'content-type': 'application/json'})
            amount_to_delete -= 1

def publish_to_storageaccount(account_conn_str,content_file_location):
    from azure.storage.blob import BlobServiceClient
    container = '$web'
    blob_client = BlobServiceClient.from_connection_string(account_conn_str)
    my_blob = blob_client.get_blob_client(container=container, blob='index.html')
    my_blob.delete_blob(delete_snapshots='include')
    with open(content_file_location, "rb") as blob:
        my_blob.upload_blob(blob)
        
# We can start by publishing to confluence.
publish_to_confluence(user=user, token=token,url=url,page_id=page_id,title='List of configurations deployed',content=text)

# Then we can remove older versions of our document, we can decide on how many versions we want to retain.
clean_old_versions(user=user,token=token,url=url,threshold=2)

# We can also publish the html file to an Azure storage account and serve it as an static website.
publish_to_storageaccount(account_conn_str=account_conn_str,content_file_location=path_html)


