import sys
import pickle
import logging
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from airflow.models import Variable

class GoogleAPI:

    def __init__(self,
                 creds_path,
                 scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']):

        # If modifying these scopes, delete the file g_svc_act.pickle.
        self.scopes = scopes
        self.creds_path = creds_path
        self.pickle_path = '%sg_oauth_clt.pickle' % (creds_path)
        self.gdrive_instance = None # lazy load
        self.gsheet_instance = None # lazy load

    def delete_token(self):
        os.remove(self.pickle_path)
        
    def generate_token(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.pickle_path):
            with open(self.pickle_path, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.warn('Google OAuth token expired... refreshing.')
                creds.refresh(Request())
            else: # FIXME: This will launch a web server inside docker.. not working
                logging.warn('Google OAuth Token %s not found' % self.pickle_path)
                flow = InstalledAppFlow.from_client_secrets_file(Variable.get('g_oauth_json_file'), self.scopes)
                flow = InstalledAppFlow.from_client_config(self.config, self.scopes)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.pickle_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def gsheet(self):
        if self.gsheet_instance is None:
            # cache_discovery=False fixes superfluous import errors
            self.gsheet_instance = build('sheets', 'v4', credentials=self.generate_token(), cache_discovery=False)
        return self.gsheet_instance

    def update_gsheet_values(self, sheet_id, sheet_range, values):
        gsheet = self.gsheet()
        logging.info('Updating gsheet values %s at %s' % (sheet_id, sheet_range))
        return gsheet.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=sheet_range,
            valueInputOption='USER_ENTERED', body={'values': values}).execute()

    def gdrive(self):
        if self.gdrive_instance is None:
            # cache_discovery=False fixes superfluous import errors
            self.gdrive_instance = build('drive', 'v3', credentials=self.generate_token(), cache_discovery=False)
        return self.gdrive_instance

    def find_gdrive_file(self, keyword, mime_type=None):
        gdrive = self.gdrive()
        logging.info('Finding gdrive file %s (%s)' % (keyword, mime_type))
        results = gdrive.files().list(q="(name contains '%s') and (mimeType = '%s')" % (keyword, mime_type),
                                      spaces='drive',
                                      pageSize=100,
                                      fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)").execute()
        return results.get('files', [])

    def delete_gdrive_file(self, file_name, mime_type=None):
        gdrive = self.gdrive()
        files = self.find_gdrive_file(file_name, mime_type)
        for f in files:
            if f['name'] == file_name:
                logging.info('Deleting gdrive file [%s] %s' % (f['id'], f['name']))
                gdrive.files().delete(fileId=f['id']).execute()

    def upload_gdrive_file(self, path_to_file, file_name, mime_type, parent_dir_id=None):
        gdrive = self.gdrive()
        if parent_dir_id is None:
            parents = []
        else:
            parents = [parent_dir_id]
        file_metadata = {
            'name': file_name,
            'parents': parents
        }
        media = MediaFileUpload(path_to_file, mimetype=mime_type, resumable=True)
        logging.info('Uploading gdrive file %s' % file_name)
        return gdrive.files().create(body=file_metadata, media_body=media, fields='id').execute()

def create_token_pickle():
    if len(sys.argv) != 2:
        print('Usage details: lib_google_api.py <path_to_credentials>')
        sys.exit()
    else:
        print('Opening browser and using %s as credentials' % sys.argv[1])
        scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], scopes)
        creds = flow.run_local_server(port=0)

        with open('credentials/g_oauth_clt.pickle', 'wb') as token:
            pickle.dump(creds, token)

if __name__ == '__main__':
    create_token_pickle()
