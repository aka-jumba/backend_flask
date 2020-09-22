from flask import Flask, request, redirect, jsonify, send_file, Response
import flask
import pandas as pd
from flask_cors import CORS
import os
import os.path
import zipfile
import uuid

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['FILE_UPLOAD'] = os.path.join(os.getcwd(),'uploads')
app.config['FILE_DOWNLOAD'] = os.path.join(os.getcwd(),'downloads')
app.config['ALLOWED_EXTENTIONS'] = ['XLSX']

'''
    in this task we store the uploaded file in the uploads folder

    intput: file excel sheet expected
    returns: json of response
'''
@app.route('/api/upload', methods = ["POST"])
def uploadController():
    if request.method == 'POST':
        if (request.files):
            incomingFile = request.files['file']
            filename = incomingFile.filename
            if (not allowedExt(filename)):
                return Response("Wrong type of file found", 422);
            s = str(uuid.uuid4()) + '.xlsx'
            incomingFile.save(os.path.join(app.config['FILE_UPLOAD'], s))
            print("image saved")
            return  jsonify(message = "upload completed", filename = s)

    return jsonify(message = "upload not completed")

'''
    in this task we find three dataset children based on given constraint

    intput: file name as query parameter
    returns: zipped excel file of the children datasets formed
'''

@app.route('/api/taskOne', methods = ["GET"])
def taskOneController():
    # first task
    if request.method == 'GET':
        filename = request.args.get('filename')
        if (filename == ''):
            return Response("This filename doesn't exist", 422)
        
        path = find(filename, app.config['FILE_UPLOAD'])
        if (path == ''):
            return Response("This filename doesn't exist", 422)

        originalDf = pd.read_excel(path)
        if ('Accepted Compound ID' not in originalDf.columns):
            return Response("This file has no \'Accepted Compound ID\' column name. Please check your file", 423)

        getChildDataFrames(originalDf, filename);
        return makeZip(list({'pcDataFrame_' + filename, 'lpcDataFrame_' + filename, 'plasmalogenDataFrame_' + filename}), 1)        
                    
    # return jsonify(message = "upload not completed")

'''
    in this task we round off the retention value

    intput: file name as query parameter
    returns: zipped excel file of augmented dataset
'''
@app.route('/api/taskTwo', methods = ["GET"])
def taskTwoController():
    # second task
    if request.method == 'GET':
        filename = request.args.get('filename')
        if (filename == ''):
            return Response("This filename doesn't exist", 422)
        
        path = find(filename, app.config['FILE_UPLOAD'])
        if (path == ''):
            return Response("This filename doesn't exist", 422)
        
        originalDf = pd.read_excel(path)
        if ('Retention time (min)' not in originalDf.columns):
            return Response("This file has no \'Retention time (min)\' column name. Please check your file", 423)
        originalDf['Retention Time Roundoff (in mins)'] = originalDf['Retention time (min)'].round()
        originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'augmentedRetentionDataFrame_' + filename), index = False)

        return makeZip(list({'augmentedRetentionDataFrame_' + filename}), 2)  
    # return "taskTwo completed"

'''
    in this task we take mean of all corresponding samples whos roundoff retention value is same

    intput: file name as query parameter
    returns: zipped excel files of the resultant dataframe
'''
@app.route('/api/taskThree', methods = ["GET"])
def taskThreeController():
    # third task
    if request.method == 'GET':
        filename = request.args.get('filename')
        filepath = find(filename, app.config['FILE_UPLOAD'])
        if (filepath == ''):
            return Response("This filename doesn't exist", 422)
        path = find('augmentedRetentionDataFrame_' + filename, app.config['FILE_DOWNLOAD'])
        print("the path is ", path)
        if (path == ''):
            return Response("Complete the second task first", 432);
        originalDf = pd.read_excel(path)
        uniqueRetentionTime = originalDf['Retention Time Roundoff (in mins)'].unique()

        metaboliteData = originalDf.drop(['m/z', 'Retention time (min)', 'Accepted Compound ID'], axis = 1)
        meanDf = pd.DataFrame(columns = metaboliteData.columns)
        index = 0;
        for val in uniqueRetentionTime:
            row = metaboliteData[metaboliteData['Retention Time Roundoff (in mins)'] == val].mean(axis = 0)
            meanDf.loc[index] = row;
            index += 1

        meanDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'meanDfDataFrame_' + filename), index = False)

        return makeZip(list({'meanDfDataFrame_' + filename}), 3) 
        

@app.route('/api/')
def default():
    return "default behaviour"

def find(name, path):
    '''
    finds if the given 'name' file exist in the path or not. 
    intput: name of the file, path where it has to be searched
    returns: Returns "" if no such file exist. Returns file path if present.
    '''
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return "";
def allowedExt(image):
    '''
    checks if . is present in the file name and if it is allowed by our business logic.
    intput: file name 
    returns: true if ext in image is correct and vice versa
    '''
    if '.' not in image:
        return False
    ext = image.split('.')[-1];
    if (ext.upper() not in app.config['ALLOWED_EXTENTIONS']):
        return False
    return True
def getChildDataFrames(originalDf, filename):
    '''
     makes the required files and download them in local download directory
     intput: dataframe required, filename given by user as query parameter
     returns: nothing
    '''
    filtered_pc_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]PC$", na = False)]
    filtered_lpc_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]LPC$", na = False)]
    filtered_plasmalogen_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]plasmalogen$", na = False)]

    filtered_pc_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'pcDataFrame_' + filename), index = False)
    filtered_lpc_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'lpcDataFrame_' + filename), index = False)
    filtered_plasmalogen_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'plasmalogenDataFrame_' + filename), index = False)
    
def makeZip(contentList, id):
    '''
    given list of files, zip them and send it back to frontend.
    intput: list of files, id of task
    returns: zipped file
    '''
    name = "";
    if (id == 1):
        name = "taskOneResponse.zip"
    elif (id == 2):
        name = "taskTwoResponse.zip"
    elif (id == 3):
        name = "taskThreeResponse.zip"
    
    zipf = zipfile.ZipFile(name,'w', zipfile.ZIP_DEFLATED)
    for file in contentList:
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], file))
    zipf.close()
    return send_file(name,
                mimetype = 'zip',
                attachment_filename= name,
                as_attachment = True) 


if __name__ == "__main__":
    # check if download and uploads folders are present or not
    if (not os.path.isdir(app.config['FILE_DOWNLOAD'])):
        os.mkdir(app.config['FILE_DOWNLOAD'])

    if (not os.path.isdir(app.config['FILE_UPLOAD'])):
        os.mkdir(app.config['FILE_UPLOAD'])
    app.run(debug=True, port=5000)