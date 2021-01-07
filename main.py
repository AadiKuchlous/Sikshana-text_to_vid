#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3

import os
import sys
import boto3
import openpyxl


def aws_polly(text, data_type):
	client = boto3.client('polly')
	if data_type == "json":
		response = client.synthesize_speech(
			LanguageCode='en-IN',
			OutputFormat='json',
			Text=text,
			SpeechMarkTypes=['word'],
			VoiceId='Raveena'
		)
	elif data_type == "mp3":
		response = client.synthesize_speech(
			LanguageCode='en-IN',
			OutputFormat='mp3',
			Text=text,
			VoiceId='Raveena'
		)

	return(response['AudioStream'])

def polly_audio(text):
	audio_data = aws_polly(text, "mp3")
	return(audio_data)

def polly_json(text):
	json_data = aws_polly(text, "json")
	return(json_data)

def create_images(text):
	words = text.split(' ')
	prefix = ""
	images = []
	for i in range(len(words)):
		if words[i] in "-:":
			continue
		prefix = ' '.join(words[0:i])
		highlighted_word = '<span style="color:red;">' + words[i] + '</span>'
		suffix = ' '.join(words[i + 1: len(words)])
		img = '<div style="height: 360px; display: flex; justify-content: center; align-items: flex-end; padding: 10px"><img src="img.jpg" style="width: 350px;"></img></div>'
		br = '<br>'
		text = '<div style="height: 360px; display: flex; justify-content: center; align-items: flex-start;"><p>{}</p></div>'.format(prefix + ' ' + highlighted_word + ' ' + suffix)
		html = '<!DOCTYPE html><html><body><div id="vid_area" style="height: 720px; width: 1280px;"><h1 style="font-size: 3.5rem">{0}{1}{2}</h1></div></body></html>'.format(img, br, text)
		with open("tmp.html", "w") as f:
			f.write(html)
		cmd = "node pup.js file://{0}/tmp.html images/{1}.jpg".format(os.getcwd(), str(i))
		os.system(cmd)
		images.append("images/{}.jpg".format(i))
	
	return(images)

def concatenate_videos(videos, output_name):
	with open('con.in', 'w') as f:
		for video in videos:
			f.write("file '{}'\n".format(video))
	os.system("ffmpeg -y -f concat -safe 0 -i con.in -strict -2 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {}".format(output_name))

def create_para_vid(speed, i, time_data, images, audio, output_name):
	end_times = []
	time_data_l = 0
	for l in time_data.iter_lines():
		time = int(l.decode().split(",")[0][8:])/(1000) * (1/speed)
		time_data_l +=1
		end_times.append(time)

	end_times = end_times[1:]

	with open("ffmp.in", "w") as f:
		prev_time = 0.0
		for j in range(len(images)-1):
			duration = float(end_times[j]) - prev_time
			f.write("file {0}' \n".format(images[j]))
			f.write("duration {} \n".format(duration))
			prev_time = float(end_times[j])

		f.write("file '{0}' \n".format(images[-1]))
		f.write("duration {} \n".format(prev_time+0.5))
	os.system("ffmpeg -y -i {0} -f concat -i ffmp.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}nf.mp4".format(audio, output_name))
	with open('blank.in', 'w') as f:
		f.write('\n'.join(["file '{0}'".format(images[-1]), "duration {}".format("1")]))
	os.system("ffmpeg -y -i {0} -f concat -i blank.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 fill{1}.mp4".format("blank.mp3", str(i)))
	output_name_mp4 = output_name + '.mp4'
	concatenate_videos(['{0}nf.mp4'.format(output_name), 'fill{}.mp4'.format(i)], output_name_mp4)

def create_vids_from_excel(file_dir):
	os.system('mkdir images')
	create_intro_video(file_dir)
	normal_videos = []
	slow_videos = []
	split_videos = []
	sheet = read_excel(file_dir)
	start = 3
	end = sheet.max_row+1
	for i in range(start, end):
		para = sheet.cell(row=i, column=1).value
		polly_para = para.replace('*', '.')
		json_data = polly_json(polly_para)
		json_data_slow = polly_json(polly_para)
		audio_data = polly_audio(polly_para)
		with open('audio_uf.mp3', 'wb') as f:
			f.write(audio_data.read())
		os.system("ffmpeg -y -i {} -ar 48000 {}".format("audio_uf.mp3", "audio.mp3"))
		os.system("sox audio.mp3 audio_slow.mp3 tempo 0.75")
		split_para = '. '.join(para.split())
		json_data_split = polly_json(split_para)
		audio_data_split = polly_audio(split_para)
		with open('audio_uf.mp3', 'wb') as f:
			f.write(audio_data_split.read())
		os.system("ffmpeg -y -i {} -ar 48000 {}".format("audio_uf.mp3", "audio_split.mp3"))
		images = create_images(para.replace('*', ''))

		create_para_vid(1, i-start+1, json_data, images, 'audio.mp3', "vid{}".format(str(i-start+1)))
		# create_para_vid(0.75, i-2, json_data_slow, 'audio_slow.mp3', "vid{}-slow".format(str(i-2)))
		# create_para_vid(1, i-2, json_data_split, 'audio_split.mp3', "vid{}-split".format(str(i-2)))

		normal_videos.append("vid{}.mp4".format(str(i-start+1)))
		slow_videos.append("vid{}-slow.mp4".format(str(i-start+1)))
		split_videos.append("vid{}-split.mp4".format(str(i-start+1)))

	os.system("mkdir final_videos")

	concatenate_videos(["intro.mp4"]+normal_videos, "final_videos/final.mp4")
	# concatenate_videos(slow_videos, "final_videos/final_slow.mp4")
	# concatenate_videos(split_videos, "final_videos/final_split.mp4")

	# os.system("rm *.mp4")
	# os.system("rm a*.mp3")

def create_intro_video(file):
	sheet = read_excel(file)
	text = (sheet.cell(row=2, column=1).value).split('\n')
	audio_data = polly_audio('. '.join(text))
	with open('audio_uf.mp3', 'wb') as f:
			f.write(audio_data.read())
	os.system("ffmpeg -y -i {} -ar 48000 {}".format("audio_uf.mp3", "intro_audio.mp3"))
	with open('intro.in', 'w') as f:
		f.write('\n'.join(["file \'images/{0}.jpg\'".format("intro"), "duration {}".format(5)]))
	headers = ''
	for line in text:
		headers += '<h1 style="font-size:2.5rem">{}</h1>'.format(line)
	html = '<!DOCTYPE html><html><body><div id="vid_area" style="height: 720px; width:1280px; display: flex; flex-direction: column; justify-content: center; align-items: center;">{}</div></body></html>'.format(headers)
	with open("intro.html", "w") as f:
			f.write(html)
	os.system("node pup.js file://{0}/intro.html images/{1}.jpg".format(os.getcwd(), "intro"))
	os.system("ffmpeg -y -i {0} -f concat -i intro.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}.mp4".format("intro_audio.mp3", "intronf"))
	with open('blank.in', 'w') as f:
		f.write('\n'.join(["file \'images/{0}.jpg\'".format("intro"), "duration {}".format("2.5")]))
	os.system("ffmpeg -y -i {0} -f concat -i blank.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 fill{1}.mp4".format("blank.mp3", "intro"))
	concatenate_videos(["intronf.mp4", "fillintro.mp4"], "intro.mp4")
	return("intro.mp4")


def read_excel(path):
	wb = openpyxl.load_workbook(path)
	return(wb["Sheet1"])

create_vids_from_excel("input.xlsx")