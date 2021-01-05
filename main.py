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
		prefix = ' '.join(words[0:i])
		highlighted_word = '<span style="color:red;">' + words[i] + '</span>'
		suffix = ' '.join(words[i + 1: len(words)])
		img = '<div style="height: 720; display: -webkit-box; -webkit-box-pack: center;"><img src="img.jpg" style="width: 200px;"></img>'
		br = '<br>'
		html = img + br + prefix + ' ' + highlighted_word + ' ' + suffix + '</div>'
		with open("tmp.html", "w") as f:
			f.write(html)
		cmd = "node --trace-warnings pup.js file://{0}/tmp.html images/{1}.jpg".format(os.getcwd(), str(i))
		images.append("images/{}".format(i))
		os.system(cmd)

def concatenate_videos(videos, output_name):
	with open('con.in', 'w') as f:
		for video in videos:
			f.write("file '{}'\n".format(video))
	os.system("ffmpeg -y -f concat -safe 0 -i con.in -strict -2  -max_muxing_queue_size 2048 -tune animation -crf 6 {}".format(output_name))

def create_para_vid(speed, i, time_data, audio, output_name):
	end_times = []
	time_data_l = 0
	for l in time_data.iter_lines():
		time = int(l.decode().split(",")[0][8:])/(1000) * (1/speed)
		time_data_l +=1
		end_times.append(time)

	end_times = end_times[1:]

	with open("ffmp.in", "w") as f:
		prev_time = 0.0
		for j in range(len(end_times)):
			duration = float(end_times[j]) - prev_time
			f.write("file \'images/{0}.jpg\' \n".format(j))
			f.write("duration {} \n".format(duration))
			prev_time = float(end_times[j])

		f.write("file \'images/{0}.jpg\' \n".format(len(end_times)))
		f.write("duration {} \n".format(prev_time+0.5))
	os.system("ffmpeg -y -i {0} -f concat -i ffmp.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}".format(audio, "mid.mp4"))
	os.system('ffmpeg -y -i mid.mp4 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1:color=white" {0}nf.mp4'.format(output_name))
	with open('blank.in', 'w') as f:
		f.write('\n'.join(["file \'images/{0}.jpg\'".format(time_data_l-1), "duration {}".format("1")]))
	os.system("ffmpeg -y -i {0} -f concat -i blank.in -strict -2 -vsync vfr -pix_fmt yuv420p -vf fps=24 -video_track_timescale 90000 -max_muxing_queue_size 2048 -tune animation -crf 6 {1}".format("blank.mp3", "mid.mp4"))
	os.system('ffmpeg -y -i mid.mp4 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1:color=white" fill{}.mp4'.format(str(i+1)))
	output_name_mp4 = output_name + '.mp4'
	concatenate_videos(['{0}nf.mp4'.format(output_name), 'fill{}.mp4'.format(str(i+1))], output_name_mp4)

def create_vids_from_text(file_dir):
	text = open(file_dir, "r").read()
	paras = text.split('\n')
	normal_videos = []
	slow_videos = []
	split_videos = []
	for i in range(len(paras)):
		para = paras[i]
		json_data = polly_json(para)
		json_data_slow = polly_json(para)
		audio_data = polly_audio(para)
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
		images = create_images(para)

		create_para_vid(1, i, json_data, 'audio.mp3', "vid{}".format(str(i+1)))
		create_para_vid(0.75, i, json_data_slow, 'audio_slow.mp3', "vid{}-slow".format(str(i+1)))
		create_para_vid(1, i, json_data_split, 'audio_split.mp3', "vid{}-split".format(str(i+1)))

		normal_videos.append("vid{}.mp4".format(str(i+1)))
		slow_videos.append("vid{}-slow.mp4".format(str(i+1)))
		split_videos.append("vid{}-split.mp4".format(str(i+1)))

	os.system("mkdir final_videos")

	concatenate_videos(normal_videos, "final_videos/final.mp4")
	concatenate_videos(slow_videos, "final_videos/final_slow.mp4")
	concatenate_videos(split_videos, "final_videos/final_split.mp4")

	os.system("rm *.mp4")
	os.system("rm a*.mp3")

def create_intro_video(file):
	#wb = load_workbook(filename = file)
	pass


create_vids_from_text("text_input.txt")