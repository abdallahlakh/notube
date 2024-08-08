from flask import Flask, request, render_template_string, jsonify
import requests
import openai
import os
import json

app = Flask(__name__)

def process_video(url):
    try:
        # Check if the URL contains 'v='
        if 'v=' in url:
            video_id = url.split('v=')[1]
        elif 'si=' in url:
            video_id = url.split('si=')[1]
        else:
            print("Invalid YouTube URL. 'v=' or 'si=' parameter not found.")
            return "Invalid YouTube URL. 'v=' or 'si=' parameter not found."


        # Define the headers with your RapidAPI key and host
        headers = {
            "x-rapidapi-key": "4f941543edmsh746dde95955d7adp166a3ejsnae2f11d94b55",
            "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
        }

        # Step 1: Get the subtitle URL for the video
        details_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
        details_querystring = {"videoId": video_id}

        details_response = requests.get(details_url, headers=headers, params=details_querystring)
        video_details = details_response.json()

        # Check if the subtitle URL is available
        if 'subtitles' in video_details and len(video_details['subtitles']['items']) > 0:
            english_subtitles = [item for item in video_details['subtitles']['items'] if item['text'] == 'English']
            
            if english_subtitles:
                subtitle_url = english_subtitles[0]['url']
                
                # Step 2: Request the subtitles using the subtitle URL
                subtitles_response = requests.get(subtitle_url)
                
                # Save the subtitles to a file
                with open('subtitles.txt', 'w', encoding='utf-8') as file:
                    file.write(subtitles_response.text)
                    file.write("\ngive me the essential keys of this video ")
                
                print("Subtitles downloaded and saved to subtitles.txt successfully.")
                
                # Send the subtitles to OpenAI API
                send_subtitles_to_openai('subtitles.txt')
            else:
                print("English subtitles are not available for this video.")
                return "English subtitles are not available for this video."
        else:
            print("Subtitles are not available for this video.")
            return "Subtitles are not available for this video."
    except Exception as e:
        print(f"An error occurred: {e}")
        return str(e)

def send_subtitles_to_openai(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            subtitles = file.read()
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": subtitles}
            ]
        )
        
        response_message = response.choices[0].message['content'].strip()
        
        # Enumerate the essential keys and write them in a readable format
        essential_keys = response_message.split('\n')
        formatted_response = "\n".join([f"{key.strip()}" for i, key in enumerate(essential_keys)])
        
        # Write the formatted response to a JSON file
        with open('response_chars.json', 'w') as json_file:
            json.dump({"formatted_response": formatted_response}, json_file)
        
        print("OpenAI API response saved to response_chars.json")
    except FileNotFoundError:
        print(f"File {file_path} not found. Please ensure the file exists.")
    except Exception as e:
        print(f"An error occurred while communicating with OpenAI API: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        error = process_video(video_url)
        if error:
            return f"An error occurred: {error}", 500
        
        # Read the response from the JSON file
        try:
            with open('response_chars.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
                formatted_response = data.get("formatted_response", "")
                
                # Convert the formatted response to HTML
                formatted_response_html = formatted_response.replace("\n", "<br>")
                
                # HTML template to display the response
                html_template = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Formatted Response</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background-color: #f4f4f4;
                        }}
                        h1 {{
                            color: #333;
                        }}
                        p {{
                            background: #fff;
                            padding: 15px;
                            border-radius: 5px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        }}
                    </style>
                </head>
                <body>
                    <h1>Essential Keys</h1>
                    <p>{formatted_response_html}</p>
                </body>
                </html>
                """
                return render_template_string(html_template)
        except FileNotFoundError:
            return "File response_chars.json not found.", 404
        except Exception as e:
            return f"An error occurred: {e}", 500
    
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enter YouTube URL</title>
    </head>
    <body>
        <h1>Enter YouTube URL</h1>
        <form method="post">
            <label for="video_url">YouTube Video URL:</label>
            <input type="text" id="video_url" name="video_url" required>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
