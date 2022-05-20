import re
import subprocess as sp
from queue import Queue
from threading import Thread
import cv2
import numpy as np
import requests
import streamlink
import logging


class StreamingServerSource:
 
    @staticmethod
    def create_stream_pipe(url, resolution):
        if url == None:
            return None

        try:
            streams = streamlink.streams(url)
        except streamlink.exceptions.NoPluginError:
            logging.warning(f"Warning: NO STREAM AVAILABLE in {url}")
            return None
        chosen_res = None
        for r in resolution:
            if r in streams and hasattr(streams[r],"url"):
                stream_url = streams[r].url
                chosen_res = r
                break

        pipe = sp.Popen(
            [
                "/usr/local/bin/ffmpeg",
                "-i",
                stream_url,
                "-loglevel",
                "quiet",  # no text output
                "-an",  # disable audio
                "-f",
                "image2pipe",
                "-pix_fmt",
                "bgr24",
                "-vcodec",
                "rawvideo",
                "-",
            ],
            stdin=sp.PIPE,
            stdout=sp.PIPE,
        )
        return pipe,chosen_res

    @staticmethod
    def read(streamer,width,height):
        raw_image = streamer.stdout.read(
                    height * width * 3
                )
        frame = np.fromstring(raw_image, dtype="uint8").reshape(
            (height, width, 3)
        )
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

    @staticmethod
    def record_video(streamer,width,height,length,filename):
        count_frame = 0
        lengthFrames = length * 30  # Assuming 30 frames per second
        frames = np.zeros((lengthFrames,height,width,3),dtype=np.uint8)
        while count_frame < lengthFrames:
            raw_image = streamer.stdout.read(
                height * width * 3
            )  

            frames[count_frame] = np.fromstring(raw_image, dtype="uint8").reshape(
                (height, width, 3)
            ).astype(np.uint8)
            count_frame += 1
        writer = cv2.VideoWriter(
            filename,
            fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
            fps=30,
            frameSize=(width, height),
            isColor=True,
        )
        for frame in frames:
            writer.write(frame)
        writer.release()

class AngelCamSource(StreamingServerSource):
    resolutions = {"best": {"width": 1920, "height": 1080}}

    @staticmethod
    def open(url):
        c = requests.get(url).content.decode("utf-8")
        m3u8 = re.findall(r"\'https://.*angelcam.*token=.*\'", c)[0].strip("'")
        streamer,chosen_res =  StreamingServerSource.create_pipe(m3u8,["best"])
        res = AngelCamSource.resolutions[chosen_res]
        width,height = res["width"],res["height"]
        return streamer,width,height
      
    @staticmethod
    def capture_image(url):
        streamer, width, height =  AngelCamSource.open(url)  
        frame = StreamingServerSource.read(streamer,width,height)
        streamer.kill()
        return True,frame

    @staticmethod
    def record_video(url,length,filename):
        streamer, width, height =  AngelCamSource.open(url)  
        frame = StreamingServerSource.record_video(streamer,width,height,length,filename)
        streamer.kill()
        return True

class YoutubeSource(StreamingServerSource):
    resolutions = {
        "240p": {"width": 426, "height": 240},
        "360p": {"width": 640, "height": 360},
        "480p": {"width": 854, "height": 480},
        "720p": {"width": 1280, "height": 720},
        "1080p": {"width": 1920, "height": 1080},
    }
    @staticmethod
    def open(url):
        streamer,chosen_res = StreamingServerSource.create_stream_pipe(url, ["1080p","720p","480p","360p","240p"])
        res = YoutubeSource.resolutions[chosen_res]
        width,height = res["width"],res["height"]
        return streamer,width,height
    
    @staticmethod
    def capture_image(url):
        streamer, width, height =  YoutubeSource.open(url)  
        frame = StreamingServerSource.read(streamer,width,height)
        streamer.kill()
        return frame
    
    
    @staticmethod
    def record_video(url,length,filename):
        streamer, width, height =  YoutubeSource.open(url)  
        frame = StreamingServerSource.record_video(streamer,width,height,length,filename)
        streamer.kill()
        return True

class RTSPSource:
            
    @staticmethod
    def open(ipv4,port,username,password):
        url = f"rtsp://"
        if username != "":
            url += f'{username}:{password}@'
        url += f'{ipv4}:{port}/Streaming/Channels/1'
        streamer = cv2.VideoCapture(url)
        return streamer


    @staticmethod
    def capture_image(ipv4,port,username,password):
        streamer = RTSPSource.open(ipv4,port,username,password)
        ret,frame = streamer.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        streamer.release()
        return frame
    
    @staticmethod
    def record_video(ipv4,port,username,password,length,filename):
        streamer = RTSPSource.open(ipv4,port,username,password)
        width = int(streamer.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(streamer.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        count_frame = 0
        lengthFrames = length * 30  # Assuming 30 frames per second
        frames = np.zeros((lengthFrames,height,width,3))

        while True:
            ret,frame = RTSPSource.read(streamer)
            if not ret:
                break
            frames[count_frame]  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            count_frame += 1
            
        streamer.release()
        writer = cv2.VideoWriter(
            filename,
            fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
            fps=30,
            frameSize=(width, height),
            isColor=True,
        )
        for frame in frames:
            writer.write(frame)
        writer.release()
        return True


def capture_image_from_streaming_server(url):
    if "youtube" in url:
        return YoutubeSource.capture_image(url)
    elif "angelcam" in url:
        return AngelCamSource.capture_image(url)

def capture_image_from_rtsp(host,port,username,password):
    return RTSPSource.capture_image(host,port,username,password)

def capture_image(camera):
    if "url" in camera:
        return capture_image_from_streaming_server(camera["url"])
    else:
        return capture_image_from_rtsp(camera["host"],camera["port"],camera["username"],camera["password"])

def record_video_from_streaming_server(url,length,outputpath):
    if "youtube" in url:
        return YoutubeSource.record_video(url,length,outputpath)
    elif "angelcam" in url:
        return AngelCamSource.record_video(url,length,outputpath)

def record_video_from_rtsp(host,port,username,password,length,outputpath):
    return RTSPSource.record_video(host,port,username,password,length,outputpath)

def record_video(camera,length,outputpath):
    if "url" in camera:
        return record_video_from_streaming_server(camera["url"],length,outputpath)
    else:
        return record_video_from_rtsp(camera["host"],camera["port"],camera["username"],camera["password"],length,outputpath)
