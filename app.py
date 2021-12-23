from flask import Flask, render_template, url_for, request, redirect, session
import json
import os
import boto3
import botocore

app                     = Flask(__name__)
app.secret_key = 'randomValue'
user = {"username": "", "password": ""}

with open('config.json', 'r') as f:
    config  = json.loads(f.read().strip())

    # endpoint                = config['endpoint']
    # accessKey               = config['accessKey']
    # secretAccessKey         = config['secretAccessKey']
    bucketName              = config['bucketName']
    region                  = config['region']
    presignedURLExpiration  = config['presignedURLExpiration']

def s3ClientCall():
    try:
        s3  = boto3.client('s3',
            # aws_access_key_id       = accessKey,
            # aws_secret_access_key   = secretAccessKey,
            # endpoint_url            = endpoint,
            region_name             = region
        )

        return(s3)

    except ValueError as e:
        return(str(e))
        
        
#Step – 4 (creating route for login)
@app.route('/', methods = ['POST', 'GET'])
def login():
    if(request.method == 'POST'):
        username = request.form.get('username')
        password = request.form.get('password')     
        if username == user['username'] and password == user['password']:
            
            session['user'] = username
            return redirect('/s3online')

        return "<h1>Wrong username or password</h1>"    

    return render_template("login.html")


@app.route('/s3online', methods=['POST', 'GET'])
def index():
    if('user' in session and session['user'] == user['username']):
        clientCall      = s3ClientCall()
    
        try:
            bucketObjects   = clientCall.list_objects(
                Bucket      = bucketName,
                Delimiter   = '/',
            )
    
            print()
            print("[#] All directories/objects in main dir: ")
            print(bucketObjects)
            print()
    
            objects = []
            dirs    = []
    
            if 'ResponseMetadata' in bucketObjects and bucketObjects['ResponseMetadata']['HTTPStatusCode'] == 200:
                if "Contents" in bucketObjects:
                    for files in bucketObjects['Contents']:
                        bucketKeys  = files['Key']
                        print(bucketKeys)
                        objects.append(bucketKeys)
    
                if "CommonPrefixes" in bucketObjects:
                    for directories in bucketObjects['CommonPrefixes']:
                        bucketDirs  = directories['Prefix']
                        print(bucketDirs)
                        dirs.append(bucketDirs)
    
            else:
                print("[!] There was some issue fetching the contents of the bucket")
    
            print(request.method, request)
            # return bucketKeys, bucketDirs
            return render_template('index.html', files=objects, directories=dirs)
    
        except botocore.exceptions.ParamValidationError as e:
            return render_template('error.html', exception=e)
    
        except botocore.exceptions.ClientError as e:
            return render_template('error.html', exception=e)
    
        except AttributeError:
            return render_template('error.html', exception=clientCall)
            
    return '<h1>You are not logged in.</h1>' 
@app.route('/list', methods=['GET'])
def list():
    if('user' in session and session['user'] == user['username']):
        clientCall      = s3ClientCall()
        directory       = request.args.get('directory')
    
        bucketObjects   = clientCall.list_objects(
            Bucket      = bucketName,
            Delimiter   = '/',
            Prefix      = directory,
        )
    
        objects = []
        dirs    = []
    
        if 'ResponseMetadata' in bucketObjects and bucketObjects['ResponseMetadata']['HTTPStatusCode'] == 200:
            if "Contents" in bucketObjects:
                for files in bucketObjects['Contents']:
                    bucketKeys  = files['Key']
                    print(bucketKeys)
                    objects.append(bucketKeys)
    
            if "CommonPrefixes" in bucketObjects:
                for directories in bucketObjects['CommonPrefixes']:
                    bucketDirs  = directories['Prefix']
                    print(bucketDirs)
                    dirs.append(bucketDirs)
    
        else:
            print("[!] There was some issue fetching the contents of the bucket")
    
        print(request.method, request)
        # return bucketKeys, bucketDirs
        return render_template('index.html', files=objects, directories=dirs)
        
    return '<h1>You are not logged in.</h1>' 

@app.route('/play', methods=['GET'])
def play():
    if('user' in session and session['user'] == user['username']):
        clientCall      = s3ClientCall()
    
        objectName      = request.args.get('name')
        print(objectName, type(objectName))
    
        presignedURL    = clientCall.generate_presigned_url('get_object',
            Params      = {
                'Bucket': bucketName,
                'Key': objectName
            },
            ExpiresIn   = presignedURLExpiration
        )
    
        print()
        print(f"[#] Presigned URL: {presignedURL}")
        print()
    
        return render_template('play.html', videoURL=presignedURL, objectName=objectName)
        
    return '<h1>You are not logged in.</h1>' 
#Step -6(creating route for logging out)
@app.route('/logout')
def logout():
    session.pop('user')         
    return redirect('/')    
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)
    app.run(debug = True)
