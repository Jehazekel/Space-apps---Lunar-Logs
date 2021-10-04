from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

import datetime
import random
db = SQLAlchemy()

class User(UserMixin, db.Model):
  id= db.Column(db.Integer, unique= True, default= random.randint(6, 100000000) )
  email= db.Column('email', db.String(120), nullable=False, primary_key=True)
  password= db.Column( 'password', db.String(120), nullable=True)
  username= db.Column( "username", db.String(20), nullable=False, unique=True )
  Logs = db.relationship( "Log" , backref="user", lazy=True)

  def set_password(self, password):
    self.password = generate_password_hash(password, method='sha256')

  def check_password(self, password):
    return check_password_hash(self.password, password)

  def toDict(self):
    return {
      'id': self.id,
      'email' : self.email,
      'username' : self.username,
      'Logs': [log.toDict() for log in self.Logs]
    }


#Everything listed in the model is on the project site
class Log(db.Model):
  
  id= db.Column(db.Integer, primary_key=True, default= random.randint(6, 100000000))
  author = db.Column( db.String(50),  db.ForeignKey('user.username'), nullable= False )
  topic = db.Column( db.String(50), nullable=False)
  text_entry = db.Column( db.String(120), nullable=True )
  time = db.Column( db.DateTime, nullable= False, default=datetime.datetime.utcnow )
  sample_type = db.Column( db.String(50), nullable=True )
  hardware_used = db.Column( db.String(50), nullable=True )
  files = db.relationship( "File" , backref="log", lazy=True) #this will be a foriegn key
  
  def getId(self):
    return self.id

  def toDict(self):
    return {
      'id':  self.id,
      'author': self.author,
      'topic' : self.topic,
      'text_entry' : self.text_entry,
      'time' : self.time.strftime("%Y-%m-%d  %H:%M:%S"),
      'sameple_type' : self.sample_type,
      'hardware_used' : self.hardware_used,
      'files': [file.toDict() for file in self.files]
    }


class File(db.Model):
  id= db.Column(db.Integer, primary_key=True, default= random.randint(6, 100000000))
  fileType = db.Column( db.String(50), nullable=False )
  filename= db.Column( db.String(120), nullable=False )
  logId = db.Column( db.Integer, db.ForeignKey('log.id'), unique=True, nullable=False)

  def set_logId(self, logId):
    self.logId = logId

    
  def toDict(self):
    return {
      'id':  self.id,
      'file': self.fileType,
      'filename' : self.filename,
      'logId': self.logId
    }
#other models, like use & file modles to be created later