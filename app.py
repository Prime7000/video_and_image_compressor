from flask import Flask, render_template,request,redirect,jsonify,send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import cv2
import shutil

app = Flask(__name__)
# Set upload folder
UPLOAD_FOLDER = os.path.join('media', 'uploads')
COMPRESS_FOLDER = os.path.join('media', 'compress')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ensure folder exists
os.makedirs(COMPRESS_FOLDER, exist_ok=True)  # ensure folder exists

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESS_FOLDER'] = COMPRESS_FOLDER


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/image')
def images():
    return render_template('image.html')


import ffmpeg

def compress_video(input_path, output_path, crf=23,video_bitrate='100k',audio_bitrate='32k',preset='medium'):
    try:
        (
            ffmpeg
            .input(input_path)
            # .output(output_path, vcodec='libx264', crf=crf, preset=preset)
            .output(output_path, vcodec='libx264', crf=crf, preset=preset,video_bitrate=video_bitrate, audio_bitrate=audio_bitrate)#optinal adding bitrate
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}")    

def clear_folder(folder_path):
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # remove file or link
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # remove directory
        except Exception as e:
            print(f"Failed to delete {item_path}. Reason: {e}")

@app.route('/video', methods=['GET', 'POST'])
def videos():
    if request.method == 'POST':
        # deleteing all existing compress video
        clear_folder(COMPRESS_FOLDER)
        clear_folder(UPLOAD_FOLDER)
        # Access file
        file = request.files.get('video')  # the key should match your FormData key
        # Access other form data    
        crf = request.form.get('crf')
        preset = request.form.get('preset')
        video_bitrate = request.form.get('video_bitrate')
        audio_bitrate = request.form.get('audio_bitrate')
        video_output = request.form.get('video_output')

        print('----------------------------------------------')
        print(f'File: {file.filename if file else "No file"}')
        print(f'CRF: {crf}, Preset: {preset}')
        print(f'Video Bitrate: {video_bitrate}, Audio Bitrate: {audio_bitrate}, Output: {video_output}')

        # Do your processing here...
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # ------------------------------
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Define compressed output filename
            name, ext = os.path.splitext(filename)
            compressed_filename = f"{filename}_compressed.{video_output}" if video_output else f"{name}_compressed.mp4"
            output_path = os.path.join(app.config['COMPRESS_FOLDER'], compressed_filename)

            if video_bitrate == None:
                video_bitrate == '100k'
            if audio_bitrate == None:
                audio_bitrate == '30k'

            # Compress video 
            compress_video(
                input_path,
                output_path,
                crf=int(crf),
                preset=preset,
                video_bitrate=video_bitrate,
                audio_bitrate=audio_bitrate
            )

            print('complete------------------')

            #-------------------getting video details------------
            cap = cv2.VideoCapture(output_path)
            if not cap.isOpened():
                print('cannot open video')
            else:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                print(f'{width}x{height}')
            cap.release()

            #-----------------getting video size--------------
            video_path = output_path
            # Get file size in bytes
            size_bytes = os.path.getsize(video_path)
            # Convert to megabytes (MB)
            size_mb = size_bytes / (1024 * 1024)
            print(f"Video size: {size_mb:.2f} MB")

            # getting the compress ratio
            ratio = round((1 - (size_bytes / os.path.getsize(input_path))) * 100, 2)
            print(f'ratio-------------------{ratio}')

        response_data = {"status": "success", "message": "Video uploaded", "filename":compressed_filename,"size":f"{size_mb:.2f} MB",'dimemsion':f'{width}x{height}', 'reduced_ratio':ratio }
        return jsonify(response_data)
    else:
        return render_template('video.html')

@app.route('/video/<filename>')
def get_video(filename):
    try:
        return send_from_directory(COMPRESS_FOLDER, filename)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run(debug=True, port=5000)