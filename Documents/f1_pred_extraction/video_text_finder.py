import cv2
import pytesseract
import csv
import os
import datetime
import time
import glob
import json

class VideoAnalyzer:
    def __init__(self, video_path, text_to_find, start_time, end_time):
        self.video = cv2.VideoCapture(video_path)
        self.text_to_find = text_to_find
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.start_frame = self.time_to_frames(start_time)
        self.end_frame = self.time_to_frames(end_time)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        self.output_folder = os.path.splitext(video_path)[0]

    def time_to_frames(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return int((datetime.timedelta(hours=h, minutes=m, seconds=s).total_seconds()) * self.fps)

    def frames_to_time(self, frames):
        seconds = frames / self.fps
        return str(datetime.timedelta(seconds=seconds))

    def analyze(self):
        start_time = time.time()
        os.makedirs(self.output_folder, exist_ok=True)
        output_file_path = os.path.join(self.output_folder, 'timestamps.csv')

        with open(output_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp"])
            print(f"Working on {self.output_folder}")
            
            while True:
                if self.video.get(cv2.CAP_PROP_POS_FRAMES) > self.end_frame:
                    break
                ret, frame = self.video.read()
                
                if not ret:
                    break

                height, _, _ = frame.shape
                frame_to_parse = frame[height//2:]

                extracted_text = pytesseract.image_to_string(frame_to_parse)

                for text in self.text_to_find:
                    if text in extracted_text:
                        timestamp = self.frames_to_time(self.video.get(cv2.CAP_PROP_POS_FRAMES))
                        print(f'Text found at {timestamp}')

                        writer.writerow([timestamp])

                        # Save the frame as an image
                        frame_file_path = os.path.join(self.output_folder, f'{self.video.get(cv2.CAP_PROP_POS_FRAMES)}.png')
                        cv2.imwrite(frame_file_path, frame)

                self.video.set(cv2.CAP_PROP_POS_FRAMES, self.video.get(cv2.CAP_PROP_POS_FRAMES) + self.fps*7)
            print(f"Analysis complete. Results saved to {output_file_path}")
            print(f"Time taken: {time.time() - start_time} seconds")
            
class VideoFolderAnalyzer:
    def __init__(self, folder_path, info_file_path):
        self.folder_path = folder_path
        self.info_file_path = info_file_path

    def check(self):
        with open(self.info_file_path, 'r') as file:
            data = json.load(file)

            text_to_find = data['text_to_find']
            if not text_to_find:
                print("No text to find specified.")

            for video_name, times in data['videos'].items():
                start_time, end_time = times
                if not self.is_valid_time(start_time) or not self.is_valid_time(end_time):
                    print(f"Invalid start or end time for video {video_name}. Start and end times should be in HH:MM:SS format.")
                    continue

                found_video = False
                for _, _, files in os.walk(self.folder_path):
                    if video_name in files:
                        found_video = True
                        break

                if not found_video:
                    print(f"Video file does not exist: {video_name}")
                    continue

                print(f"Info is valid for video {video_name}")

    def is_valid_time(self, time_str):
        try:
            h, m, s = map(int, time_str.split(':'))
            datetime.time(h, m, s)
            return True
        except ValueError:
            return False

    def analyze(self):
        with open(self.info_file_path, 'r') as file:
            data = json.load(file)
            text_to_find = data['text_to_find']
            for video_name, times in data['videos'].items():
                start_time, end_time = times
                for root, dirs, files in os.walk(self.folder_path):
                    if video_name in files:
                        video_path = os.path.join(root, video_name)
                        analyzer = VideoAnalyzer(video_path, text_to_find, start_time, end_time)
                        analyzer.analyze()
                        break



folder_analyzer = VideoFolderAnalyzer("/Volumes/Bruh/f1/2023_races", "/Users/macbook/Documents/f1_pred_extraction/2023.json")
#folder_analyzer.check()
folder_analyzer.analyze()