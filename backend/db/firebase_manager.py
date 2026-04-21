import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseManager:
    def __init__(self):
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
            fallback_path = os.path.join(os.path.dirname(__file__), "..", "..", "serviceAccountKey.json")
            
            active_path = cred_path if os.path.exists(cred_path) else (fallback_path if os.path.exists(fallback_path) else None)
            
            if active_path:
                absolute_cred_path = os.path.abspath(active_path)
                cred = credentials.Certificate(absolute_cred_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.is_connected = True
            else:
                print(f"Warning: serviceAccountKey.json not found. Running in mock mode.")
                self.db = None
                self.is_connected = False

    def get_user_by_email(self, email):
        if not self.is_connected: return None
        users = self.db.collection('Users').where('email', '==', email).limit(1).get()
        if users:
            data = users[0].to_dict()
            data['uid'] = users[0].id
            return data
        return None

    def create_user(self, email, password, uid, role="user"):
        if not self.is_connected: return False
        self.db.collection('Users').document(uid).set({
            'email': email,
            'password': password, # Plaintext for prototype assignment (In production, hash this!)
            'role': role,
            'created': datetime.datetime.utcnow()
        })
        return True

    def log_session_start(self, user_id, session_id):
        if not self.is_connected: return
        self.db.collection('Sessions').document(session_id).set({
            'user_id': user_id,
            'logintime': datetime.datetime.utcnow(),
            'logouttime': None
        })

    def log_session_end(self, session_id):
        if not self.is_connected: return
        self.db.collection('Sessions').document(session_id).update({
            'logouttime': datetime.datetime.utcnow()
        })

    def log_query(self, user_id, session_id, question, answer, uploaded_filename=None):
        if not self.is_connected: return
        self.db.collection('Queries').add({
            'userid': user_id,
            'sessionid': session_id,
            'question': question,
            'answer': answer,
            'user_uploaded_file_name': uploaded_filename,
            'timestamp': datetime.datetime.utcnow()
        })

    def get_recent_queries(self, session_id, limit=50):
        if not self.is_connected: return []
        queries_ref = self.db.collection('Queries')
        # Removed order_by to prevent 'Requires composite index' crash on Firestore
        results = queries_ref.where('sessionid', '==', session_id).get()
        docs = [doc.to_dict() for doc in results]
        docs.sort(key=lambda x: str(x.get('timestamp', '')), reverse=False)
        return docs[-limit:] if docs else []

firebase_manager = FirebaseManager()
