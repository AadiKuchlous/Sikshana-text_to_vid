from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_autoindex import AutoIndex
import tempfile
import openpyxl
import os


app = Flask(__name__)
files_index = AutoIndex(app, os.path.curdir + '/videos', add_url_rules=False)

@app.route('/', methods=["GET", "POST"])
def index():
	pass

@app.route('/new', methods=["GET", "POST"])
def new_xl_form():
	return render_template('xlform.html')

@app.route('/new_data', methods=["GET", "POST"])
def new_vid_data():
	file = request.files['file']
	fileName = secure_filename(file.filename)
	tmpdir = tempfile.mkdtemp()
	file.save(os.path.join(tmpdir, 'input.xlsx'))
	os.chdir(tmpdir)
	wb = openpyxl.load_workbook(fileName)
	sheets = wb.sheetnames
	return render_template('dataform.html', header="", sheets=sheets)

@app.route('/form_submit', methods=["GET", "POST"])
def form_submit():
	print("in form_submit")
	if request.method == "POST":
		print("got POST")
		sheetName = request.form["sheetName"]
		videoName = request.form["name"]
		file = request.files['file']
		fileName = secure_filename(file.filename)

		if os.path.exists("videos/{}".format(videoName)):
			return render_template('form.html', header="Videos with this name already exist")
		else:
			tmpdir = tempfile.mkdtemp()
			file.save(os.path.join(tmpdir, 'input.xlsx'))
			print(tmpdir)
			cmd = 'main.py' + ' ' + 'input.xlsx' + ' ' + '"{}"'.format(str(sheetName)) + ' ' + '"{}"'.format(str(tmpdir)) + ' ' + '"{}"'.format(str(videoName)) #+ ' &'
			print(cmd)
			os.system(cmd)
			return 'File: ' + fileName + '; Sheet Name: ' + sheetName + '; Video Name: ' + videoName + '; Name available'

@app.route('/files')
@app.route('/files/<path:path>')
def autoindex(path='.'):
	return files_index.render_autoindex(path)