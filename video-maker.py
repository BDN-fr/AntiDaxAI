import cv2
import os

image_folder = 'ai-vision'

images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
images.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

shape = cv2.imread(os.path.join(image_folder, images[0])).shape

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_output = cv2.VideoWriter('output.mp4', fourcc, 5.0, (shape[1], shape[0]))

for image in images:
    frame = cv2.imread(os.path.join(image_folder, image))
    frame = cv2.resize(frame, (shape[1], shape[0]))
    video_output.write(frame)

video_output.release()
