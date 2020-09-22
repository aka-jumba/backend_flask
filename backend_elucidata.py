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


def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return "";
def allowedExt(image):
    if '.' not in image:
        return False
    ext = image.split('.')[-1];
    if (ext.upper() not in app.config['ALLOWED_EXTENTIONS']):
        return False
    return True


@app.route('/api/upload', methods = ["POST"])
def uploadController():
    if request.method == 'POST':
        if (request.files):
            image = request.files['file']
            filename = image.filename
            if (not allowedExt(filename)):
                return Response("Wrong type of file found", 422);
            s = str(uuid.uuid4()) + '.xlsx'
            image.save(os.path.join(app.config['FILE_UPLOAD'], s))
            print("image saved")
            return  jsonify(message = "upload completed", filename = s)

    return jsonify(message = "upload not completed")

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
        filtered_pc_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]PC$", na = False)]
        filtered_lpc_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]LPC$", na = False)]
        filtered_plasmalogen_originalDf = originalDf[originalDf['Accepted Compound ID'].str.contains(".*[_ ]plasmalogen$", na = False)]

        filtered_pc_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'pcDataFrame_' + filename), index = False)
        filtered_lpc_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'lpcDataFrame_' + filename), index = False)
        filtered_plasmalogen_originalDf.to_excel(os.path.join(app.config['FILE_DOWNLOAD'], 'plasmalogenDataFrame_' + filename), index = False)
        zipf = zipfile.ZipFile('taskOneResponse.zip','w', zipfile.ZIP_DEFLATED)
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], 'pcDataFrame_' + filename))
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], 'pcDataFrame_' + filename))
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], 'plasmalogenDataFrame_' + filename))
        zipf.close()
        return send_file('taskOneResponse.zip',
                mimetype = 'zip',
                attachment_filename= 'taskOneResponse.zip',
                as_attachment = True)            
    # return jsonify(message = "upload not completed")

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
        zipf = zipfile.ZipFile('taskTwoResponse.zip','w', zipfile.ZIP_DEFLATED)
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], 'augmentedRetentionDataFrame_' + filename))
        zipf.close()
        return send_file('taskTwoResponse.zip',
                mimetype = 'zip',
                attachment_filename= 'taskTwoResponse.zip',
                as_attachment = True)
    # return "taskTwo completed"


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
        zipf = zipfile.ZipFile('taskThreeResponse.zip','w', zipfile.ZIP_DEFLATED)
        zipf.write(os.path.join(app.config['FILE_DOWNLOAD'], 'meanDfDataFrame_' + filename))
        zipf.close()
        return send_file('taskThreeResponse.zip',
                mimetype = 'zip',
                attachment_filename= 'taskThreeResponse.zip',
                as_attachment = True)
        

@app.route('/api/')
def default():
    return "default behaviour"
if __name__ == "__main__":
    if (not os.path.isdir(app.config['FILE_DOWNLOAD'])):
        os.mkdir(app.config['FILE_DOWNLOAD'])

    if (not os.path.isdir(app.config['FILE_UPLOAD'])):
        os.mkdir(app.config['FILE_UPLOAD'])
    app.run(debug=True, port=5000)