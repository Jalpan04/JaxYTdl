from flask import Flask, request, render_template_string, send_file, redirect, url_for
import yt_dlp
import os

app = Flask(__name__)

# Set your FFmpeg location here
FFMPEG_LOCATION = r'C:/Users/Jalpan/Downloads/ffmpeg-2024-11-03-git-df00705e00-full_build/ffmpeg-2024-11-03-git-df00705e00-full_build/bin'
DOWNLOAD_FOLDER = 'static/downloads'  # Ensure this folder exists

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JaxYTdl - YouTube Downloader</title>
        <style>
            /* Existing styles */
            @font-face {
                font-family: 'Bruno Ace';
                src: url('{{ url_for("static", filename="fonts/BrunoAce-Regular.woff2") }}') format('woff2'),
                    url('{{ url_for("static", filename="fonts/BrunoAce-Regular.woff") }}') format('woff');
                font-weight: normal;
                font-style: normal;
            }
            body {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Bruno Ace', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                flex-direction: column;
            }
            .container {
                text-align: center;
                padding: 20px;
                border: 1px solid #333;
                border-radius: 8px;
                background-color: #1e1e1e;
                width: 50%;
            }
            /* New styles for header */
            .header {
                position: absolute;
                top: 20px;
                left: 20px;
                display: flex;
                align-items: center;
            }
            .header h1 {
                font-size: 24px;
                margin: 0;
            }
            /* Existing input and button styles */
            input[type="text"] {
                width: 80%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #333;
                color: #fff;
            }
            input[type="submit"] {
                padding: 10px 15px;
                background-color: #333;
                color: #00acea;
                border: 1px solid #00acea;
                border-radius: 5px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #0080b3;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>JaxYTdl</h1>
        </div>
        <div class="container">
            <h1>YouTube Downloader</h1>
            <form action="/get_formats" method="post">
                <label for="url">YouTube URL:</label><br>
                <input type="text" id="url" name="url" required><br><br>
                <input type="submit" value="Get Formats">
            </form>
        </div>
    </body>
    </html>
    """



@app.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.form['url']

    ydl_opts = {
        'ffmpeg_location': FFMPEG_LOCATION,
        'format': 'bestaudio/best',
        'outtmpl': 'temp.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            thumbnail = info_dict.get('thumbnail', '')
            title = info_dict.get('title', 'video')

            filtered_formats = []
            for fmt in formats:
                if fmt['ext'] == 'mp4' and fmt.get('height') in [2160, 1440, 1080, 720, 480, 360, 240, 144]:
                    filtered_formats.append({
                        'format_id': fmt['format_id'],
                        'note': f"{fmt['height']}p (mp4)",
                        'filesize': fmt.get('filesize', None)
                    })
            filtered_formats.append({
                'format_id': 'bestaudio',
                'note': 'Audio Only (mp3)',
                'filesize': None
            })

    except Exception as e:
        return f"An error occurred while fetching formats: {str(e)}"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Select Format</title>
        <style>
            body {
                background-color: #121212;
                color: #ffffff;
                font-family: 'Bruno Ace', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 20px;
                border: 1px solid #333;
                border-radius: 8px;
                background-color: #1e1e1e;
                width: 60%;
            }
            img {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }
            select, input[type="submit"] {
                padding: 10px 15px;
                background-color: #333;
                color: #00acea;
                border: 1px solid #00acea;
                border-radius: 5px;
                cursor: pointer;
            }
           
            }
            input[type="submit"]:hover {
                background-color: #0080b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Select Download Format</h1>
            <img src="{{ thumbnail }}" alt="Video Thumbnail"><br><br>
            <form action="/download" method="post">
                <input type="hidden" name="url" value="{{ url }}">
                <input type="hidden" name="title" value="{{ title }}">
                <label for="format">Choose Format:</label><br>
                <select id="format" name="format">
                    {% for fmt in formats %}
                        <option value="{{ fmt['format_id'] }}">
                            {{ fmt['note'] }} ({{ fmt['filesize'] | filesizeformat }})
                        </option>
                    {% endfor %}
                </select><br><br>
                <input type="submit" value="Download">
            </form>
        </div>
    </body>
    </html>
    """, formats=filtered_formats, thumbnail=thumbnail, url=url, title=title)

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_id = request.form['format']
    title = request.form['title']

    # Clean title to be file system safe
    safe_title = "".join(x for x in title if (x.isalnum() or x in "._- ")).strip()

    ydl_opts = {
        'ffmpeg_location': FFMPEG_LOCATION,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{safe_title}.%(ext)s'),  # Use download folder
        'postprocessors': [],
    }

    if format_id == 'bestaudio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
    else:
        ydl_opts['format'] = f'{format_id}+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            if format_id == 'bestaudio':
                filename = filename.replace('.webm', '.mp3')
            else:
                filename = filename.replace('.webm', '.mp4')

        # Serve the file with a button to download another song
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download</title>
            <style>
                body {
                    background-color: #121212;
                    color: #ffffff;
                    font-family: 'Bruno Ace', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    flex-direction: column;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 20px;
                    border: 1px solid #333;
                    border-radius: 8px;
                    background-color: #1e1e1e;
                    width: 50%;
                }
                a, button {
                    padding: 10px 15px;
                    background-color: #333;
                    color: #00acea;
                    border: 1px solid #00acea;
                    border-radius: 5px;
                    cursor: pointer;
                }
                a:hover, button:hover {
                    background-color: #0080b3;
                }
                p {
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <p>Almost there, <a href="{{ filename }}">Click Here</a> to download.</p>
                <p><button onclick="window.location.href='/'">Download Another Song</button></p>
            </div>
        </body>
        </html>
        """, filename=filename)

    except Exception as e:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {
                    background-color: #121212;
                    color: #ffffff;
                    font-family: 'Bruno Ace', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 20px;
                    border: 1px solid #333;
                    border-radius: 8px;
                    background-color: #1e1e1e;
                    width: 50%;
                }
                a {
                    color: #6200ea;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>An Error Occurred</h1>
                <p>{{ error_message }}</p>
                <p><a href="/">Go Back</a></p>
            </div>
        </body>
        </html>
        """, error_message=str(e))

def filesizeformat(bytes, binary=False):
    if bytes is None or bytes == 0:
        return "Unknown size"

    base = 1024 if binary else 1000
    prefixes = ['KiB', 'MiB', 'GiB'] if binary else ['kB', 'MB', 'GB']
    for unit in prefixes:
        bytes /= base
        if bytes < base:
            return f"{bytes:.1f} {unit}"
    return f"{bytes:.1f} {'TiB' if binary else 'TB'}"

if __name__ == '__main__':
    app.jinja_env.filters['filesizeformat'] = filesizeformat
    app.run(debug=True)
