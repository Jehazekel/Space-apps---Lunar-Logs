import os
import json
import datetime
from flask_cors import CORS
from flask import Flask, request, jsonify, render_template, redirect, flash, url_for, send_file, send_from_directory
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError

from werkzeug.utils import secure_filename

from models.models import User, Log , File, db



#For file uploads
UPLOAD_FOLDER = os.getcwd() + '/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'png', 'jpg', 'jpeg', 'gif'}

#returns true/false for file extensions compared 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


print( '\n\n\n' + os.getcwd()  + '\n\n\n' )
print( os.path.join(UPLOAD_FOLDER, 'filename'))



''' Begin Flask Login Functions '''
login_manager = LoginManager()
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

#N.B. Remember me cookies are for the event a user logs out accidentally

#THE URL TO REDIRECTS USER TO IF THEY ARENT LOGGED IN
login_manager.login_view = "/login"
#Store the previous page that required login...and redirects user to it if true
login_manager.use_session_for_next= False

#Duration of the login_manager remember me session cookie
login_manager.REMEMBER_COOKIE_DURATION= datetime.timedelta(minutes= 1)
#Prevents client side scripts from accessing it
login_manager.REMEMBER_COOKIE_HTTPONLY= False
#Refreshes cookie on each request: if true
login_manager.REMEMBER_COOKIE_REFRESH_EACH_REQUEST= True
''' End Flask Login Functions '''


def create_app(UPLOAD_FOLDER):
  app = Flask(__name__, static_url_path='')
  #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
  DBURI = os.environ.get("DATABASE_URL")
  SQLITEDB = os.environ.get("SQLITEDB", default="true")
  app.config['ENV'] = os.environ.get("ENV")
  app.config['SQLALCHEMY_DATABASE_URI'] = DBURI
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
  app.config['SECRET_KEY'] = "MYSECRET"
  app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
  CORS(app)
  db.init_app(app)
  login_manager.init_app(app)
  return app

app = create_app(UPLOAD_FOLDER)

app.app_context().push()


socketio = SocketIO(app)

def call_page_reload():
    socketio.emit('new_log', 'reload', broadcast=True)

################# TEST ROUTES
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
  data= request.form 
  
  print('\n\n\n\n')
  print(data)
  print(type(data))
  if request.method == 'POST':
    
    # Get data from request
    
    #return json.dumps(data['username'] )
    #Create object 
    name = User(username=data['username'], email=data['email'])
    name.set_password(data['password'])

    print( name.toDict() )
    
    #add to db session and commit
    
    db.session.add(name)
    db.session.commit()
    return json.dumps( name.toDict() )
  

  
  elif request.method == 'GET':
    return app.send_static_file('test.html')
  

@app.route('/get_users', methods=['GET'])
def get_all_users():
  users = User.query.all()
  users = [user.toDict() for user in users]
  return json.dumps(users)

def get_logs():
  logs = Log.query.all()
  logs = [log.toDict() for log in logs]
  return logs

@app.route('/get_logs', methods=['GET'])
def get_all_logs():
  logs = get_logs()
  return json.dumps(logs)

@app.route('/get_files', methods=['GET'])
def get_all_files():
  files = File.query.all()
  print(files)
  files = [file.toDict() for file in files]
  print(files)
  return json.dumps(files)

@app.route('/newpage', methods=['GET'])
def newpage():
  return app.send_static_file('test.html')


###########################



#home page
@app.route('/', methods=['GET'])
@login_required
def home():
    logs = get_logs()
    return render_template('view-logs.html', logs= logs)
    

@app.route('/about', methods=['GET'])
@login_required
def about():
  return render_template("about.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if request.method == 'POST':
      data = request.form
      
      # Get data from request
    
      #return json.dumps(data['username'] )
      #Create object 
      user = User(username=data['username'], email=data['email'])
      user.set_password(data['password'])

      print( user.toDict() )
      
      #add to db session and commit
      try:
        db.session.add(user)
        db.session.commit()

        #login user
        login_user(user, remember=True, duration=datetime.timedelta(hours=1) )
        #add flash msg
        flash("Your account has successfully been created!")
        return redirect('/')

      except IntegrityError:
        print("\n\n\nUser already exist \n\n\n");
        db.session.rollback()
        #add flash msg  
        flash('Username is alreasdy in use. Please Select another')
        return redirect('/signup')
    elif request.method == 'GET':
      return render_template('sign-up.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
      data = request.form
      user = User.query.filter_by(username= data['username']).first()

      if user and user.check_password(data['password']):
        login_user( user, remember=True, duration= datetime.timedelta(hours= 1) )
        flash("You have logged in successfully")

        #redirect to url for home
        return redirect( url_for('.home') )

      else:
        #For invalid credentials
        flash("Login Failed: Invalid User email or password. ")
        return redirect( url_for('.login') )
      
    
    elif request.method == 'GET':
      return render_template('login.html')



@app.route("/logout", methods=["GET"])
@login_required
def logout():
  logout_user()
  flash('Logged Out!')
  return redirect(url_for('.login'))






@app.route("/log-entry", methods=["POST", "GET"])
@login_required
def create_log():
    if request.method == 'POST':
      
      data = request.form

      print( '\n\n\n\n ')
      print( data) 
      file = request.files['file']

      author = current_user.username
      
      if data['topic'] :
        topic = data['topic']
      else:
        topic = '' 

      if data['sample_type'] :
        sample_type = data['sample_type']
      else:
        sample_type = '' 

      if data['hardware_used'] :
        hardware_used = data['hardware_used']
      else:
        hardware_used = '' 

      if data['text_entry'] :
        text_entry = data['text_entry']
      else:
        text_entry = '' 

      newLog= Log( author= author, topic= topic, text_entry = text_entry, sample_type= sample_type, hardware_used= hardware_used )
      print('\n\n\t\tLog object has been created')
      try:
        db.session.add(newLog)
        db.session.commit()

        #upload image
        if file.filename  and file.filename != '':
          print("\t\t\tFiles find in request")
          save_uploaded_file( newLog.getId(), file)
          
          #SEND BROADCAST MESSAGE HERE

        else:
          print("\t\t\t NO Files found in request")

        call_page_reload()
        print('\n\n\t\tLog has been successfully added!!')
        return redirect('/')
 

      except IntegrityError:
        print("\n\n\LOG ENTRY ERROR: log could not be created. \n\n\n");
        db.session.rollback()
        #add flash msg  
        flash('An error occured while attempting to add your log. Please Try again!')
        return redirect('/log-entry')

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
      
    #display log page  
    elif request.method == 'GET':
      if current_user.is_authenticated:
        username = current_user.username
        return render_template('log-entry.html', username= username)

      else:
        flash('You must be logined to access this page.')
        return redirect('/login')
      

#FOR FILE UPLOADS FROM LOG-ENTRY.HTML
def save_uploaded_file(logId, file):
  # save file in uploads folder
  if file and allowed_file(file.filename):
    print('\n\n\n {}'.format(file.filename) )
    filename = secure_filename(file.filename)
    file.save( os.path.join(UPLOAD_FOLDER, filename) )

    #save file record in db as an object
    img_extensions = {'png' ,'jpg' , 'jpeg' , 'jfif' , 'pjpeg' , 'pjp', 'webp', 'svg'}

    vid_extensions = { ' mp4' }

    aud_extensions = { 'wav', 'ogg', 'mp3'}

    if filename.rsplit('.', 1)[1].lower() in img_extensions:
      fileType = 'image'

    elif filename.rsplit('.', 1)[1].lower() in vid_extensions:
      fileType = 'audio'

    elif filename.rsplit('.', 1)[1].lower() in aud_extensions:
      fileType = 'video'

    else:
      fileType = 'unknown'
    
    newFile = File(fileType=fileType, filename=filename, logId=logId)

    try: 
      db.session.add(newFile)
      db.session.commit()
      #flash('Your file, {} has been uploaded successfully.!'.format(filename))
    
    except IntegrityError:
        print("\n\n\File already exist \n\n\n");
        db.session.rollback()
        #add flash msg  
        flash('Error occur uploading File. if this error occurs again, please contact the back-end developer.')
      


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print('\n\n\n {}'.format(file.filename) )
            filename = secure_filename(file.filename)
            file.save( os.path.join(UPLOAD_FOLDER, filename) )

            
            return redirect(url_for('download_file', name= filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post action='/upload'enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


  

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
  #return send_from_directory(UPLOAD_FOLDER, name)
  

  return '''
    <!doctype html>
    <title>Download File</title>
    <h1>Download File</h1>
    <a href={} download> 
    <img src={} >
    <p>Click to download</p>
    <a/> 
    '''.format( os.path.join(UPLOAD_FOLDER, filename), os.path.join(UPLOAD_FOLDER, filename))


    

# "send" for socketio sends a msg to the event message
#where as "emit" for socketio can create custom events

@socketio.on('my event')
def handle_my_custom_event(json_data):
  print('\n\n\n\t\treceived json: ' + str(json_data['data']) + '\n\n\n')



#recieves a msg and responds on a diff channel
@socketio.on('message')
def handle_incoming_msg(msg):
  print( '\n\n\nRecieved Message: {}\n\n\n\n'.format(msg))
  
  emit('message_repsonse', {"response": msg}, broadcast=True );


@socketio.on('new_log')
def trigger_reload(msg):
  print( '\n\n\nRecieved Message: {}\n\n\n\n'.format(msg))
  
  emit('trigger_reload', {"response": 'reload'}, broadcast=True );

if __name__ == '__main__':
  #socketio.run(app, host='0.0.0.0', port=8080, debug=True )
  app.run(host='0.0.0.0', port=8080, debug=True) # socketio.run(app)
